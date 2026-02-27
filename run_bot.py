"""
Скрипт для запуска бота литературного календаря
С поддержкой команд и выбора даты через календарь
"""

import asyncio
import logging
import os
from datetime import datetime

from time_utils import now_tz
from dotenv import load_dotenv
from literary_calendar_bot import LiteraryCalendarBot
from telegram_calendar import TelegramCalendar
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError


# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class BotWithCommands:
    def __init__(self, bot_token: str, calendar_url: str, graphql_endpoint: str, timezone: str = "Europe/Moscow", send_hour: int = 9):
        self.literary_bot = LiteraryCalendarBot(
            bot_token=bot_token,
            calendar_url=calendar_url,
            graphql_endpoint=graphql_endpoint,
            timezone=timezone,
            send_hour=send_hour
        )
        self.bot_token = bot_token
        self.app: Application | None = None
        self.calendar_picker = TelegramCalendar(timezone=timezone)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        await update.message.reply_text(
            "📚 Привет! Я бот литературного календаря сервиса «Свет».\n\n"
            "📌 Доступные команды:\n"
            "/send_events_for_today - События на сегодня\n"
            "/choose_date - Выбрать дату из календаря\n"
            "/jubilee - Показать юбиляров за выбранный год\n"
            "/help - Помощь"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
    📚 <b>Бот литературного календаря</b>

    <b>Команды:</b>
    /send_events_for_today — Получить события на сегодня
    /choose_date — Выбрать дату из календаря
    /jubilee — Показать юбиляров за выбранный год
    /help — Показать эту справку

    <b>Как использовать:</b>
    1. Отправьте /send_events_for_today для событий на сегодня
    2. Отправьте /choose_date для выбора любой даты
    3. Выберите дату в календаре — получите события

    <b>О боте:</b>
    Бот показывает литературные события: дни рождения писателей, даты публикаций знаменитых книг и другие памятные даты.
    Для каждого события предоставляются ссылки на книги в приложении «Свет».
    Вопросы и предложения: svet@rsl.ru
        """
        await update.message.reply_text(help_text, parse_mode='HTML')

    async def send_events_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /send_events_for_today - отправляет события на сегодня"""
        chat_id = update.effective_chat.id
        
        await update.message.reply_text("🔍 Ищу события на сегодня...")
        await self.literary_bot.send_daily_digest(chat_id=str(chat_id))
        
        logger.info(f"Команда send_events_for_today выполнена для чата {chat_id}")

    async def jubilee_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /jubilee - открывает упрощённый селектор годов."""
        # Помечаем режим, чтобы callback знал, что это выбор года для юбилеев
        context.user_data['mode'] = 'jubilee'
        now = now_tz(self.literary_bot.timezone)
        # Показываем диапазон ±6 лет по умолчанию
        year_keyboard = self.calendar_picker.create_year_selector(start_year=now.year - 6, span=13)

        await update.message.reply_text(
            "📅 Выберите год для просмотра юбиляров:",
            reply_markup=year_keyboard
        )

        logger.info(f"Годовой селектор (jubilee) показан для чата {update.effective_chat.id}")

    async def choose_date_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /choose_date - показывает календарь"""
        calendar_keyboard = self.calendar_picker.create_calendar()
        
        await update.message.reply_text(
            "📅 Выберите дату:",
            reply_markup=calendar_keyboard
        )
        
        logger.info(f"Календарь показан для чата {update.effective_chat.id}")

    async def calendar_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий на кнопки календаря"""
        query = update.callback_query
        await query.answer()
        
        # Обрабатываем выбор
        selected, date, new_keyboard = self.calendar_picker.process_selection(query.data)
        
        if selected:
            # Дата выбрана - отправляем события
            chat_id = update.effective_chat.id
            
            # Удаляем календарь
            await query.edit_message_text(
                f"✅ Выбрана дата: {date.strftime('%d.%m.%Y')}\n"
                f"🔍 Ищу события..."
            )
            
            # Временно сохраняем выбранную дату в контексте бота
            # и получаем события на эту дату
            if context.user_data.get('mode') == 'jubilee':
                target_year = date.year

                await query.edit_message_text(
                    f"✅ Выбран год: {target_year}\n"
                    f"🔍 Ищу юбиляров..."
                )

                # Отправляем список юбиляров для года
                await self.send_jubilees_for_year(chat_id, target_year)

                # Очищаем режим
                context.user_data.pop('mode', None)

            else:
                await self.send_events_for_date(chat_id, date)
            
        elif new_keyboard:
            # Обновляем календарь (переход между месяцами/годами)
            await query.edit_message_reply_markup(reply_markup=new_keyboard)

    async def send_events_for_date(self, chat_id: int, date: datetime):
        """
        Отправляет события на выбранную дату (из календаря)
        Использует обновлённую логику send_daily_digest из literary_calendar_bot
        
        Args:
            chat_id: ID чата
            date: Выбранная дата
        """
        try:
            # Получаем события на выбранную дату
            events = await self.literary_bot.get_events_by_date(date)
            
            if not events:
                date_str = date.strftime('%d %B %Y')
                await self.literary_bot.bot.send_message(
                    chat_id=chat_id,
                    text=f"📅 <b>{date_str}</b>\n\n"
                         f"На этот день в календаре пока что нет событий.",
                    parse_mode='HTML'
                )
                return
            
            # Отправляем каждое событие отдельным сообщением (вариант А)
            for event in events:
                try:
                    # Используем новую логику из send_daily_digest
                    await self._send_event_with_media(chat_id, event)
                except Exception as inner_e:
                    logger.error(f"Ошибка отправки события '{event.get('title')}' на дату {date}: {inner_e}", exc_info=True)
                    await self.literary_bot.bot.send_message(
                        chat_id=chat_id,
                        text=f"⚠️ Не удалось отправить событие: {event.get('title')}",
                        parse_mode='HTML'
                    )
                
        except Exception as e:
            logger.error(f"Ошибка отправки событий на дату {date}: {e}", exc_info=True)
            await self.literary_bot.bot.send_message(
                chat_id=chat_id,
                text="❌ Произошла ошибка при получении событий. Попробуйте позже.",
                parse_mode='HTML'
            )

    async def send_jubilees_for_year(self, chat_id: int, year: int):
        """Получает и отправляет список юбиляров для указанного года."""
        await self.literary_bot.send_jubilees_for_year(str(chat_id), year)

    async def _send_event_with_media(self, chat_id: int, event: dict):
        """
        Отправляет одно событие с обложками (media_group) + текст.
        Использует универсальный метод из LiteraryCalendarBot.
        """
        await self.literary_bot.send_event_with_media(str(chat_id), event)

    async def setup_handlers(self):
        """Настройка обработчиков команд"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("send_events_for_today", self.send_events_command))
        self.app.add_handler(CommandHandler("choose_date", self.choose_date_command))
        self.app.add_handler(CommandHandler("jubilee", self.jubilee_command))
        
        # Обработчик для календаря
        self.app.add_handler(CallbackQueryHandler(self.calendar_callback, pattern='^cal_'))

    async def run_polling(self):
        """Запуск бота в режиме polling с корректной работой с python-telegram-bot v20"""
        print("🤖 Бот запущен в режиме polling")
        print("📚 Доступные команды:")
        print("   /start - Начать работу")
        print("   /send_events_for_today - События на сегодня")
        print("   /choose_date - Выбрать дату")
        print("   /help - Помощь")

        max_retries = 3
        retry_delay = 5  # секунд
        for attempt in range(max_retries):
            self.app = Application.builder().token(self.bot_token).build()
            await self.setup_handlers()
            try:
                logger.info(f"Попытка подключения к Telegram API (попытка {attempt + 1}/{max_retries})...")
                await self.app.initialize()
                await self.app.start()
                await self.app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
                logger.info("✅ Успешно подключено к Telegram API")
                try:
                    await asyncio.Event().wait()
                finally:
                    await self._shutdown_app()
                return
            except (TelegramError, Exception) as e:
                await self._shutdown_app()
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Ошибка подключения (попытка {attempt + 1}/{max_retries}): {e}")
                    logger.info(f"Повторная попытка через {retry_delay} секунд...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"❌ Не удалось подключиться после {max_retries} попыток")
                    raise

    async def _shutdown_app(self):
        """Останавливает приложение и освобождает ресурсы"""
        if not self.app:
            return
        try:
            await self.app.updater.stop()
        except Exception:
            pass
        try:
            await self.app.stop()
        except Exception:
            pass
        try:
            await self.app.shutdown()
        except Exception:
            pass


async def main():
    """Главная функция запуска бота"""

    load_dotenv()

    # Загрузка конфигурации
    bot_token = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    graphql_endpoint = os.getenv('GRAPHQL_ENDPOINT', 'https://example.com/graphql')
    calendar_url = os.getenv('CALENDAR_URL', '')
    timezone = os.getenv('TIMEZONE', 'Europe/Moscow')
    send_hour = int(os.getenv('SEND_HOUR', '9'))

    # Если параметры - placeholder, пробуем загрузить из конфига
    if "YOUR_BOT_TOKEN_HERE" in bot_token:
        try:
            import literary_calendar_bot_config as config
            bot_token = getattr(config, 'BOT_TOKEN', bot_token)
            graphql_endpoint = getattr(config, 'GRAPHQL_ENDPOINT', graphql_endpoint)
            calendar_url = getattr(config, 'CALENDAR_URL', calendar_url)
            timezone = getattr(config, 'TIMEZONE', timezone)
            send_hour = getattr(config, 'SEND_HOUR', send_hour)
        except ImportError:
            pass

    # Проверяем конфигурацию
    if not bot_token or "YOUR_BOT_TOKEN_HERE" in bot_token:
        print("⚠️  Предупреждение: BOT_TOKEN не настроен!")
        print("   Получите токен у @BotFather в Telegram")
        print("   Установите переменную окружения: export BOT_TOKEN='ваш_токен'")
        return
    
    if not graphql_endpoint:
        print("⚠️  Предупреждение: GRAPHQL_ENDPOINT не настроен!")
        print("   Установите переменную окружения: export GRAPHQL_ENDPOINT='ваш_api_url'")
        return
    
    # Создаем бота с поддержкой команд
    bot_with_commands = BotWithCommands(
        bot_token=bot_token,
        calendar_url=calendar_url,
        graphql_endpoint=graphql_endpoint,
        timezone=timezone,
        send_hour=send_hour
    )
    
    print("✅ Бот инициализирован")
    print(f"🔗 API: {graphql_endpoint}")
    print("\n" + "="*50)
    print("🚀 Запуск бота с поддержкой команд и календаря")
    print("="*50)

    try:
        await bot_with_commands.run_polling()
    finally:
        try:
            await bot_with_commands.literary_bot.aclose()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        print(f"\n❌ Ошибка: {e}")
        print("Проверьте логи выше для деталей")