"""
Telegram-бот для ежедневной рассылки литературных дат из календаря
с ссылками на книги из API "Свет"
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs

import httpx
from telegram import Bot, InputMediaPhoto
from telegram.error import TelegramError

from literary_calendar_database import LiteraryCalendarDatabase

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

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
    
    async def get_books_by_author(self, author_uuid: str) -> List[Dict]:
        """Получает книги автора через GraphQL API"""
        query = """
        query GetBooksByAuthor($authorUuid: String!) {
          books(body: {
            authors: [$authorUuid]
            isActive: true
            limit: 5
          }) {
            uuid
            name
            slug
            annotation
            image {
              url
            }
          }
        }
        """
        
        variables = {"authorUuid": author_uuid}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.graphql_endpoint,
                    json={"query": query, "variables": variables},
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and 'books' in data['data']:
                        return data['data']['books']
                else:
                    logger.error(f"Ошибка API: {response.status_code}")
        except Exception as e:
            logger.error(f"Ошибка запроса к API: {e}")
        
        return []
    
    async def search_books_by_title(self, title: str, author_name: str = None) -> List[Dict]:
        """Ищет книги по названию и автору через GraphQL API"""
        # Очищаем название от лишних символов
        clean_title = re.sub(r'[«»""„‟]', '', title).strip()
        
        query = """
        query SearchBooks($names: [String!]!) {
          books(body: {
            names: $names
            isActive: true
            limit: 6
          }) {
            uuid
            name
            slug
            annotation
            authors {
              uuid
            }
            image {
              url
            }
          }
        }
        """
        
        # Формируем список названий для поиска
        search_names = [clean_title]
        if author_name:
            # Также добавим версию с именем автора
            search_names.append(f"{author_name} {clean_title}")
        
        variables = {"names": search_names}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.graphql_endpoint,
                    json={"query": query, "variables": variables},
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and 'books' in data['data']:
                        books = data['data']['books']
                        logger.info(f"Найдено книг по запросу '{clean_title}': {len(books)}")
                        return books
                    else:
                        logger.warning(f"Нет данных в ответе API для запроса '{clean_title}'")
                else:
                    logger.error(f"Ошибка API поиска книг (code {response.status_code}): {response.text[:200]}")
        except Exception as e:
            logger.error(f"Ошибка запроса поиска книг: {e}")
        
        return []
    
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
        query = """
        query GetBooksByTag($tagSlug: String!) {
          tags(body: {
            slugs: [$tagSlug]
          }) {
            uuid
            name
            books(limit: 6) {
              uuid
              name
              slug
              image {
                url
              }
            }
          }
        }
        """
        
        variables = {"tagSlug": tag}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.graphql_endpoint,
                    json={"query": query, "variables": variables},
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data:
                        if 'tags' in data['data'] and data['data']['tags']:
                            tag_data = data['data']['tags'][0]
                            if 'books' in tag_data:
                                return tag_data['books']
        except Exception as e:
            logger.error(f"Ошибка запроса к API по тегу: {e}")
        
        return []

    async def get_books_by_category(self, category_uuid: str) -> List[Dict]:
        """Получает книги по категории через GraphQL API"""
        query = """
        query GetBooksByCategory($categoryUuid: String!) {
          category(body: { uuid: $categoryUuid }) {
            uuid
            name
            books(limit: 6) {
              uuid
              name
              slug
              image { 
                url 
              }
            }
          }
        }
        """

        variables = {"categoryUuid": category_uuid}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.graphql_endpoint,
                    json={"query": query, "variables": variables},
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and data['data'].get('category'):
                        books = data['data']['category'].get('books', [])
                        return books
        except Exception as e:
            logger.error(f"Ошибка запроса к API по категории: {e}")

        return []
    
    def format_event_message(self, event: Dict, books: List[Dict] = None, include_image_urls: bool = True, other_links: List[Dict] = None) -> str:
        """Форматирует сообщение о событии с ссылками на книги.

        Args:
            include_image_urls: если False, не добавлять в текст явные URL обложек
        """
        message_parts = []
        
        # Заголовок
        message_parts.append(f"📚 <b>{event['title']}</b>")
        
        # Дата (по русски)
        if event.get('start_date'):
            months = [
                'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'
            ]
            date_obj = event['start_date']
            month_name = months[date_obj.month - 1]
            date_str = f"{date_obj.day} {month_name} {date_obj.year}"
            message_parts.append(f"📅 {date_str}")
        
        # Если это день рождения - добавляем "N лет со дня рождения"
        if event.get('event_type') == 'день рождения':
            # Для дней рождения всегда пытаемся извлечь год из названия (т.к. в БД часто неправильный год)
            birth_year = None
            
            # Извлекаем год из названия события (например, "Чехов родился в 1860 году")
            year_match = re.search(r'\b(1[0-9]{3}|2[0-2][0-9]{2})\b', event.get('title', ''))
            if year_match:
                # Первый найденный год - это обычно год рождения
                birth_year = int(year_match.group(1))
            
            # Если не смогли извлечь из названия, пробуем из поля 'year', но только если оно разумное
            if not birth_year and event.get('year'):
                year_val = event.get('year')
                # Проверяем, что год выглядит разумно (1600-1999)
                if isinstance(year_val, int) and 1600 <= year_val <= 1999:
                    birth_year = year_val
            
            if birth_year:
                current_date = event.get('start_date', datetime.now())
                # Рассчитываем возраст на дату события (текущего года)
                age = current_date.year - birth_year
                
                if age > 0:  # Только если возраст положительный
                    # Проверяем, является ли это юбилеем (оканчивается на 0 или 5)
                    is_jubilee = age % 10 == 0 or age % 10 == 5
                    
                    if is_jubilee:
                        # Юбилей - выделяем жирным и подчёркиванием
                        message_parts.append(f"🎂 <u><b>🎉 {age} лет со дня рождения 🎉</b></u>")
                    else:
                        message_parts.append(f"🎂 {age} лет со дня рождения")
        
        # Описание (без обрезания)
        if event.get('description'):
            desc = event['description']
            message_parts.append(f"\n{desc}")

        # Ссылки на авторов/теги/категории (если есть)
        if other_links:
            message_parts.append("\n🔗 <b>Ссылки:</b>")
            for l in other_links:
                name = l.get('name') or ''
                url = l.get('url') or ''
                if url:
                    # Добавляем ссылку с новой строки для читаемости
                    message_parts.append(f"\n• <a href='{url}'>{name}</a>")
                else:
                    message_parts.append(f"\n• {name}")
        
        # Книги с обложками и ссылками
        if books:
            message_parts.append("\n📖 <b>Книги:</b>")
            
            for book in books[:6]:  # Максимум 6 книг
                book_name = book.get('name', 'Без названия')
                book_slug = book.get('slug', '')
                metadata = book.get('metadata', {}) or {}
                
                # Формируем ссылку на книгу
                if book_slug:
                    book_url = f"https://example.com/catalog/{book_slug}"
                    message_parts.append(f"• <a href='{book_url}'>{book_name}</a>")
                else:
                    message_parts.append(f"• {book_name}")
                
                # Добавляем информацию об обложке если есть (опционально в тексте)
                image_data = metadata.get('image', {}) or {}
                if include_image_urls and isinstance(image_data, dict):
                    image_url = image_data.get('url', '')
                    if image_url:
                        message_parts.append(f"  <i>Обложка: {image_url}</i>")
                
                # Аннотация
                annotation = metadata.get('annotation', '')
                if annotation:
                    message_parts.append(f"  <i>{annotation[:100]}</i>")
        else:
            message_parts.append("\n<i>Нет информации о книгах в каталоге</i>")
        
        return "\n".join(message_parts)
    
    async def get_today_events(self) -> List[Dict]:
        """Получает события на сегодня"""
        now = datetime.now()
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
                        event_dict['author_refs'].append({'uuid': ref_uuid, 'name': ref_name})
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
    
    async def send_daily_digest(self, chat_id: str):
        """Отправляет ежедневную рассылку с событиями и ссылками на книги"""
        try:
            events = await self.get_today_events()
            
            if not events:
                logger.info("Нет событий на сегодня")
                await self.bot.send_message(
                    chat_id=chat_id,
                    text="На сегодня в календаре пока что нет событий.",
                    parse_mode='HTML'
                )
                return
            
            # Отправляем каждое событие отдельным сообщением
            for event in events:
                books = []
                other_links = []  # ссылки на авторов/тегов/категорий для текста
                
                # 1. Сначала добавляем книги из references БД (они уже есть)
                for book_ref in event.get('book_references', []):
                    books.append({
                        'uuid': book_ref['uuid'],
                        'name': book_ref['name'],
                        'slug': book_ref['slug'],
                        'metadata': book_ref.get('metadata', {}),
                        'source': 'database'
                    })
                    logger.debug(f"Добавлена книга из БД: {book_ref['name']}")
                
                # 2. Ищем книги по названию и автору из заголовка
                book_info = self.extract_book_info_from_title(event['title'])
                if book_info['book_title']:
                    found_books = await self.search_books_by_title(
                        book_info['book_title'], 
                        book_info['author']
                    )
                    for book in found_books:
                        # Избегаем дубликатов
                        if not any(b.get('uuid') == book.get('uuid') for b in books):
                            books.append({
                                'uuid': book.get('uuid'),
                                'name': book.get('name', 'Без названия'),
                                'slug': book.get('slug', ''),
                                'metadata': {'image': book.get('image', {})},
                                'source': 'api_search'
                            })
                            logger.debug(f"Найдена книга по запросу: {book.get('name')}")
                
                # 3. Получаем книги по UUID авторов (и формируем ссылку на автора)
                for author_ref in event.get('author_refs', []):
                    au_uuid = author_ref.get('uuid')
                    au_name = author_ref.get('name') or ''
                    # ссылка на поиск по автору на сайте
                    author_url = f"https://example.com/catalog?authors={au_uuid}&page=1"
                    other_links.append({'type': 'author', 'name': au_name or 'Автор', 'url': author_url})
                    # получаем книги автора (для обложек)
                    author_books = await self.get_books_by_author(au_uuid)
                    for book in author_books:
                        if not any(b.get('uuid') == book.get('uuid') for b in books):
                            books.append({
                                'uuid': book.get('uuid'),
                                'name': book.get('name', 'Без названия'),
                                'slug': book.get('slug', ''),
                                'metadata': {'image': book.get('image', {})},
                                'source': 'author_api'
                            })
                            logger.debug(f"Найдена книга по автору: {book.get('name')}")
                
                # 4. Получаем книги по тегам (и формируем ссылки на теги)
                for tag_ref in event.get('tag_refs', []):
                    tag_uuid = tag_ref.get('uuid')
                    tag_name = tag_ref.get('name') or ''
                    tag_url = f"https://example.com/catalog?tags={tag_uuid}&page=1"
                    other_links.append({'type': 'tag', 'name': tag_name or 'Тег', 'url': tag_url})
                    tag_books = await self.get_books_by_tag(tag_uuid)
                    for book in tag_books:
                        if not any(b.get('uuid') == book.get('uuid') for b in books):
                            books.append({
                                'uuid': book.get('uuid'),
                                'name': book.get('name', 'Без названия'),
                                'slug': book.get('slug', ''),
                                'metadata': {'image': book.get('image', {})} if book.get('image') else {},
                                'source': 'tag_api'
                            })
                            logger.debug(f"Найдена книга по тегу: {book.get('name')}")
                
                # 5. Если нет ни одной ссылки - генерируем поиск по названию события
                if not other_links and not books:
                    # Генерируем URL для поиска по названию события
                    event_title_clean = event['title'].strip()
                    search_url = f"https://example.com/catalog?search={event_title_clean.replace(' ', '+')}&page=1"
                    other_links.append({'type': 'search', 'name': event_title_clean, 'url': search_url})
                    logger.debug(f"Сгенерирована ссылка поиска для события: {event_title_clean}")
                    
                    # Пытаемся найти книги по названию события через API
                    search_books = await self.search_books_by_title(event_title_clean)
                    for book in search_books[:10]:  # берём до 10 книг
                        if not any(b.get('uuid') == book.get('uuid') for b in books):
                            books.append({
                                'uuid': book.get('uuid'),
                                'name': book.get('name', 'Без названия'),
                                'slug': book.get('slug', ''),
                                'metadata': {'image': book.get('image', {})} if book.get('image') else {},
                                'source': 'auto_search'
                            })
                            logger.debug(f"Найдена книга по названию события: {book.get('name')}")
                
                # Формируем и отправляем медиа (обложки) + текст
                # Сначала собираем доступные обложки — но не больше 6
                media_items = []
                for book in books:
                    if len(media_items) >= 6:
                        break
                    metadata = book.get('metadata', {}) or {}
                    image_data = metadata.get('image', {}) or {}
                    image_url = ''
                    if isinstance(image_data, dict):
                        image_url = image_data.get('url', '')
                    elif isinstance(image_data, str):
                        image_url = image_data

                    if image_url:
                        # Ссылка на карточку книги (если есть slug)
                        book_slug = book.get('slug', '')
                        if book_slug:
                            book_url = f"https://example.com/catalog/{book_slug}"
                        else:
                            book_url = ''

                        # подпись под изображением — название (ссылка если есть)
                        caption = book.get('name', '')
                        if book_url:
                            caption = f"<a href='{book_url}'>{caption}</a>"

                        try:
                            media_items.append(InputMediaPhoto(media=image_url, caption=caption))
                        except Exception:
                            logger.debug(f"Невозможно создать InputMediaPhoto для {image_url}")

                # Если есть медиа — отправляем группу
                if media_items:
                    try:
                        # Telegram принимает до 10 медиа в группе, мы посылаем не больше 6
                        await self.bot.send_media_group(chat_id=chat_id, media=media_items[:6])
                        await asyncio.sleep(0.5)
                    except TelegramError as e:
                        logger.warning(f"Не удалось отправить media_group: {e}")

                    # После отправки картинок отправляем текст без явных URL обложек и без предпросмотра
                    message = self.format_event_message(event, books, include_image_urls=False, other_links=other_links)
                    disable_preview = True
                else:
                    # Если обложек нет — отправляем обычное текстовое сообщение (с URL обложек если они есть в metadata)
                    message = self.format_event_message(event, books, include_image_urls=True, other_links=other_links)
                    disable_preview = False

                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='HTML',
                        disable_web_page_preview=disable_preview
                    )
                    logger.info(f"Отправлено событие: {event['title']} (книг: {len(books)})")
                    await asyncio.sleep(1)
                except TelegramError as e:
                    logger.error(f"Ошибка отправки сообщения: {e}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке рассылки: {e}", exc_info=True)
    
    async def run_daily(self):
        """Запускает бота в режиме ежедневной рассылки"""
        logger.info("Бот запущен в режиме ежедневной рассылки")
        
        while True:
            try:
                now = datetime.now()
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
    from literary_calendar_bot_config import (
        BOT_TOKEN,
        CALENDAR_URL,
        GRAPHQL_ENDPOINT,
        SEND_HOUR,
        TIMEZONE
    )

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