"""
Telegram-бот для ежедневной рассылки литературных дат из календаря
с ссылками на книги из API "Свет"
"""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv
from telegram import Bot

from bot.formatting import (
    extract_image_url_from_metadata,
    format_event_message,
    get_age_word,
)
from clients.graphql_client import GraphQLClient
from literary_calendar_database import LiteraryCalendarDatabase
from time_utils import now_tz
from services.digest_service import DigestService
from services.jubilee_service import JubileeService

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class LiteraryCalendarBot:
    """Бот для рассылки литературных дат"""
    
    def __init__(
        self,
        bot_token: str,
        calendar_url: str,
        graphql_endpoint: str,
        timezone: str = "Europe/Moscow",
        send_hour: int = 9
    ):
        """
        Инициализация бота
        
        Args:
            bot_token: Токен Telegram бота
            calendar_url: URL календаря Yandex Calendar
            graphql_endpoint: URL GraphQL API
            timezone: Часовой пояс
            send_hour: Время отправки дайджеста (в часах)
        """
        self.bot = Bot(token=bot_token)
        self.calendar_url = calendar_url
        self.graphql_endpoint = graphql_endpoint
        self.timezone = timezone
        self.send_hour = send_hour
        self._gql = GraphQLClient(graphql_endpoint)
        self._digest = DigestService(bot=self.bot, gql=self._gql, timezone=self.timezone)
        self._jubilees = JubileeService(bot=self.bot)

    async def aclose(self):
        await self._gql.aclose()
    
    @staticmethod
    def extract_image_url_from_metadata(metadata) -> str:
        return extract_image_url_from_metadata(metadata)

    @staticmethod
    def get_age_word(age: int) -> str:
        return get_age_word(age)

    async def get_books_by_author(self, author_uuid: str) -> List[Dict]:
        """Получает книги автора через GraphQL API"""
        return await self._gql.get_books_by_author(author_uuid)

    async def get_books_by_author_slug(self, author_slug: str) -> List[Dict]:
        """Получает книги автора по slug через GraphQL API (фолбэк, если uuid не даёт результата)"""
        return await self._gql.get_books_by_author_slug(author_slug)
    
    async def get_book_by_uuid(self, book_uuid: str) -> Optional[Dict]:
        """Получает информацию о книге по UUID через GraphQL API"""
        return await self._gql.get_book_by_uuid(book_uuid)
    
    async def search_books_by_title(self, title: str, author_name: str = None) -> List[Dict]:
        """Ищет книги по названию и автору через GraphQL API"""
        return await self._gql.search_books_by_title(title=title, author_name=author_name)
    
    def extract_book_info_from_title(self, title: str) -> Dict[str, str]:
        """Извлекает название книги и автора из заголовка события"""
        result = {'author': None, 'book_title': None}
        
        # Ищем книгу в кавычках
        book_match = re.search(r'[«»""„‟]([^«»""„‟]+)[«»""„‟]', title)
        if book_match:
            result['book_title'] = book_match.group(1).strip()
        
        # Ищем автора
        title_without_quotes = re.sub(r'[«»""„‟][^«»""„‟]+[«»""„‟]', '', title)
        author_match = re.search(r'([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+){1,2})', title_without_quotes)
        if author_match:
            result['author'] = author_match.group(1).strip()
        
        logger.info(f"Извлечено из '{title}': автор='{result['author']}', книга='{result['book_title']}'")
        return result
    
    async def get_books_by_tag(self, tag: str) -> List[Dict]:
        """Получает книги по тегу через GraphQL API"""
        return await self._gql.get_books_by_tag(tag)

    async def get_books_by_category(self, category_uuid: str) -> List[Dict]:
        """Получает книги по категории через GraphQL API"""
        return await self._gql.get_books_by_category(category_uuid)
    
    def format_event_message(self, event: Dict, books: List[Dict] = None, include_image_urls: bool = True, other_links: List[Dict] = None) -> str:
        return format_event_message(
            event=event,
            timezone=self.timezone,
            books=books,
            include_image_urls=include_image_urls,
            other_links=other_links,
        )
    
    async def get_today_events(self) -> List[Dict]:
        """Получает события на сегодня"""
        now = now_tz(self.timezone)
        return await self.get_events_by_date(now)
    
    async def get_events_by_date(self, date: datetime) -> List[Dict]:
        """
        Получает события на указанную дату из базы и обогащает их информацией о книгах из API
        
        Args:
            date: Дата для получения событий
        
        Returns:
            Список событий с ссылками на книги
        """
        try:
            # Пытаемся получить из встроенной в этот модуль базы данных
            db = LiteraryCalendarDatabase()
            events = db.get_events_by_date(date.month, date.day)
            db.close()
            
            # Преобразуем в формат бота и обогащаем информацией о книгах
            result = []
            for event in events:
                event_dict = {
                    'title': event['title'],
                    'description': event.get('description', ''),
                    'start_date': date,
                    'event_type': event.get('event_type', ''),  # Тип события (birthday, death, etc.)
                    'year': event.get('year'),  # Год рождения/смерти для расчёта юбилеев
                    'author_refs': [],   # [{'uuid':..., 'name':...}]
                    'book_uuids': [],
                    'book_references': [],  # Полные данные о книгах из БД
                    'tag_refs': [],       # [{'uuid':..., 'name':...}]
                    'category_refs': []   # [{'uuid':..., 'name':...}]
                }

                # Обработка ссылок (references) из БД
                for ref in event.get('references', []):
                    ref_type = ref.get('reference_type')
                    ref_uuid = ref.get('reference_uuid')
                    ref_name = ref.get('reference_name')
                    metadata = ref.get('metadata', {}) or {}

                    if ref_type == 'author' and ref_uuid:
                        event_dict['author_refs'].append({
                            'uuid': ref_uuid, 
                            'name': ref_name,
                            'slug': ref.get('reference_slug', '')
                        })
                        logger.debug(f"Добавлен автор: {ref_name} ({ref_uuid})")

                    elif ref_type == 'book' and ref_uuid:
                        event_dict['book_uuids'].append(ref_uuid)
                        book_ref = {
                            'uuid': ref_uuid,
                            'slug': ref.get('reference_slug', ''),
                            'name': ref_name or 'Без названия',
                            'metadata': metadata
                        }
                        event_dict['book_references'].append(book_ref)
                        logger.debug(f"Добавлена книга: {ref_name}")

                    elif ref_type == 'tag' and ref_uuid:
                        event_dict['tag_refs'].append({'uuid': ref_uuid, 'name': ref_name})
                        logger.debug(f"Добавлен тег: {ref_name}")

                    elif ref_type == 'category' and ref_uuid:
                        event_dict['category_refs'].append({'uuid': ref_uuid, 'name': ref_name})

                result.append(event_dict)
            
            logger.info(f"Найдено событий на {date.day}.{date.month}: {len(result)}")
            return result
            
        except ImportError:
            logger.warning("База данных недоступна")
            return []
        except Exception as e:
            logger.error(f"Ошибка получения событий: {e}", exc_info=True)
            return []

    async def get_jubilees_for_year(self, year: int) -> List[Dict]:
        """Возвращает список юбиляров для указанного года (возраст и ссылки)."""
        try:
            db = LiteraryCalendarDatabase()
            jubilees = db.get_jubilees_by_year(year)
            db.close()
            return jubilees
        except Exception as e:
            logger.error(f"Ошибка получения юбиляров: {e}", exc_info=True)
            return []
    
    async def send_jubilees_for_year(self, chat_id: str, year: int):
        """Получает и отправляет список юбиляров для указанного года с разбивкой по месяцам."""
        jubilees = await self.get_jubilees_for_year(year)
        await self._jubilees.send_jubilees_for_year(chat_id=chat_id, year=year, jubilees=jubilees)
    
    async def collect_books_and_links(self, event: Dict) -> Tuple[List[Dict], List[Dict]]:
        return await self._digest.collect_books_and_links(event)
    
    async def send_event_with_media(self, chat_id: str, event: Dict):
        await self._digest.send_event_with_media(chat_id, event)
    
    async def send_daily_digest(self, chat_id: str):
        """Отправляет ежедневную рассылку с событиями и ссылками на книги"""
        try:
            events = await self.get_today_events()
            
            if not events:
                logger.info("Нет событий на сегодня")
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="На этот день в календаре пока что нет событий.",
                    parse_mode='HTML'
                )
                return
            
            # Отправляем каждое событие отдельным сообщением
            for event in events:
                await self.send_event_with_media(chat_id, event)
            
        except Exception as e:
            logger.error(f"Ошибка при отправке рассылки: {e}", exc_info=True)
    
    async def run_daily(self):
        """Запускает бота в режиме ежедневной рассылки"""
        logger.info("Бот запущен в режиме ежедневной рассылки")
        
        while True:
            try:
                now = now_tz(self.timezone)
                if now.hour == self.send_hour and now.minute == 0:
                    # Здесь нужен chat_id для отправки
                    logger.warning("Автоматическая рассылка требует chat_id. Используйте /send_events_for_today")
                    await asyncio.sleep(3600)
                else:
                    await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Ошибка в цикле: {e}")
                await asyncio.sleep(60)


async def main():
    """Главная функция для запуска бота"""
    load_dotenv()
    from literary_calendar_bot_config import (
        BOT_TOKEN,
        CALENDAR_URL,
        GRAPHQL_ENDPOINT,
        SEND_HOUR,
        TIMEZONE
    )

    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан. Укажите его в переменных окружения или в файле .env")

    bot = LiteraryCalendarBot(
        bot_token=BOT_TOKEN,
        calendar_url=CALENDAR_URL,
        graphql_endpoint=GRAPHQL_ENDPOINT,
        timezone=TIMEZONE,
        send_hour=SEND_HOUR
    )
    
    logger.info("Бот инициализирован")


if __name__ == "__main__":
    asyncio.run(main())