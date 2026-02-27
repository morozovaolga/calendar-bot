"""
Модуль для создания inline-календаря в Telegram
Позволяет пользователю выбрать дату для просмотра событий
"""

import calendar
from datetime import datetime, timedelta
from typing import List, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from time_utils import now_tz


class TelegramCalendar:
    """Класс для создания inline-календаря в Telegram"""
    
    MONTHS_RU = [
        "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
        "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
    ]
    
    DAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    
    def __init__(self, timezone: str = "Europe/Moscow"):
        self.calendar = calendar.Calendar(firstweekday=0)  # Неделя начинается с понедельника
        self.timezone = timezone
    
    @staticmethod
    def create_callback_data(action: str, year: int = None, month: int = None, day: int = None) -> str:
        """
        Создаёт callback_data для кнопки
        
        Формат: ACTION;YEAR;MONTH;DAY
        Например: DAY;2024;12;25
        """
        return f"cal_{action};{year or 0};{month or 0};{day or 0}"
    
    @staticmethod
    def parse_callback_data(callback_data: str) -> Tuple[str, int, int, int]:
        """Парсит callback_data"""
        parts = callback_data.replace("cal_", "").split(";")
        action = parts[0]
        year = int(parts[1]) if len(parts) > 1 else 0
        month = int(parts[2]) if len(parts) > 2 else 0
        day = int(parts[3]) if len(parts) > 3 else 0
        return action, year, month, day
    
    def create_calendar(self, year: int = None, month: int = None) -> InlineKeyboardMarkup:
        """
        Создаёт клавиатуру-календарь для выбора даты
        
        Args:
            year: Год (по умолчанию текущий)
            month: Месяц (по умолчанию текущий)
        
        Returns:
            InlineKeyboardMarkup с календарём
        """
        now = now_tz(self.timezone)
        if year is None:
            year = now.year
        if month is None:
            month = now.month
        
        keyboard = []
        
        # Заголовок: месяц и год
        header_row = [
            InlineKeyboardButton("<<", callback_data=self.create_callback_data("PREV_MONTH", year, month)),
            InlineKeyboardButton(f"{self.MONTHS_RU[month-1]} {year}", callback_data="cal_IGNORE"),
            InlineKeyboardButton(">>", callback_data=self.create_callback_data("NEXT_MONTH", year, month))
        ]
        keyboard.append(header_row)
        
        # Дни недели
        weekdays_row = [InlineKeyboardButton(day, callback_data="cal_IGNORE") for day in self.DAYS_RU]
        keyboard.append(weekdays_row)
        
        # Дни месяца
        month_calendar = self.calendar.monthdayscalendar(year, month)
        for week in month_calendar:
            row = []
            for day in week:
                if day == 0:
                    # Пустая ячейка
                    row.append(InlineKeyboardButton(" ", callback_data="cal_IGNORE"))
                else:
                    # Проверяем, не прошла ли эта дата
                    date = datetime(year, month, day)
                    if date.date() == now.date():
                        # Сегодня — выделяем
                        row.append(InlineKeyboardButton(f"•{day}•", callback_data=self.create_callback_data("DAY", year, month, day)))
                    else:
                        # Любая другая дата — доступна
                        row.append(InlineKeyboardButton(str(day), callback_data=self.create_callback_data("DAY", year, month, day)))
            keyboard.append(row)
        
        # Нижние кнопки
        bottom_row = [
            InlineKeyboardButton("« Год назад", callback_data=self.create_callback_data("PREV_YEAR", year, month)),
            InlineKeyboardButton("Сегодня", callback_data=self.create_callback_data("TODAY", year, month)),
            InlineKeyboardButton("Год вперёд »", callback_data=self.create_callback_data("NEXT_YEAR", year, month))
        ]
        keyboard.append(bottom_row)
        
        return InlineKeyboardMarkup(keyboard)

    def create_year_selector(self, start_year: int = None, span: int = 12) -> InlineKeyboardMarkup:
        """Создаёт упрощённый селектор годов.

        Args:
            start_year: первый год в списке (по умолчанию центрится на текущем годе)
            span: количество лет в селекторе
        """
        now = now_tz(self.timezone)
        if start_year is None:
            start_year = now.year - span // 2

        keyboard = []
        row = []
        per_row = 4
        for i, y in enumerate(range(start_year, start_year + span)):
            row.append(InlineKeyboardButton(str(y), callback_data=self.create_callback_data("YEAR", y, 0, 0)))
            if (i + 1) % per_row == 0:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        # Навигация по диапазонам
        bottom_row = [
            InlineKeyboardButton("« Предыдущие", callback_data=self.create_callback_data("CHANGE_YEARS", start_year - span, 0, 0)),
            InlineKeyboardButton("Сегодня", callback_data=self.create_callback_data("TODAY", now.year, 0, 0)),
            InlineKeyboardButton("Следующие »", callback_data=self.create_callback_data("CHANGE_YEARS", start_year + span, 0, 0))
        ]
        keyboard.append(bottom_row)

        return InlineKeyboardMarkup(keyboard)
    
    def process_selection(self, callback_data: str) -> Tuple[bool, datetime, InlineKeyboardMarkup]:
        """
        Обрабатывает нажатие на кнопку календаря
        
        Args:
            callback_data: Данные из callback
        
        Returns:
            Кортеж (завершён_выбор, выбранная_дата, новая_клавиатура)
        """
        action, year, month, day = self.parse_callback_data(callback_data)
        now = now_tz(self.timezone)
        
        if action == "IGNORE":
            return False, None, None
        
        elif action == "DAY":
            # Дата выбрана
            return True, datetime(year, month, day), None
        
        elif action == "TODAY":
            # Переход к сегодняшней дате
            return False, None, self.create_calendar(now.year, now.month)
        
        elif action == "PREV_MONTH":
            # Предыдущий месяц
            if month == 1:
                new_year = year - 1
                new_month = 12
            else:
                new_year = year
                new_month = month - 1
            return False, None, self.create_calendar(new_year, new_month)
        
        elif action == "NEXT_MONTH":
            # Следующий месяц
            if month == 12:
                new_year = year + 1
                new_month = 1
            else:
                new_year = year
                new_month = month + 1
            return False, None, self.create_calendar(new_year, new_month)
        
        elif action == "PREV_YEAR":
            # Предыдущий год
            return False, None, self.create_calendar(year - 1, month)
        
        elif action == "NEXT_YEAR":
            # Следующий год
            return False, None, self.create_calendar(year + 1, month)

        elif action == "YEAR":
            # Выбран год в селекторе годов
            return True, datetime(year, 1, 1), None

        elif action == "CHANGE_YEARS":
            # Показать другой диапазон годов (year содержит стартовый год)
            return False, None, self.create_year_selector(start_year=year)
        
        return False, None, None