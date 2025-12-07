"""
Telegram-бот для ежедневной рассылки литературных дат из календаря
с ссылками на книги из API "Свет"
"""

import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs

import httpx
from telegram import Bot
from telegram.error import TelegramError

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
        group_chat_id: str,
        timezone: str = "Europe/Moscow"
    ):
        """
        Инициализация бота
        
        Args:
            bot_token: Токен Telegram бота
            calendar_url: URL календаря Yandex Calendar
            graphql_endpoint: URL GraphQL API
            group_chat_id: ID группы в Telegram (можно получить через @userinfobot)
            timezone: Часовой пояс
        """
        self.bot = Bot(token=bot_token)
        self.calendar_url = calendar_url
        self.graphql_endpoint = graphql_endpoint
        self.group_chat_id = group_chat_id
        self.timezone = timezone
        
    async def fetch_calendar(self) -> str:
        """Загружает календарь из Yandex Calendar"""
        async with httpx.AsyncClient() as client:
            response = await client.get(self.calendar_url)
            if response.status_code == 200:
                return response.text
            else:
                raise Exception(f"Ошибка загрузки календаря: {response.status_code}")
    
    def parse_calendar(self, xml_content: str) -> List[Dict]:
        """
        Парсит XML календарь и извлекает события
        
        Returns:
            Список событий с датами и информацией
        """
        # Используем улучшенный парсер
        return self._simple_parse(xml_content)
    
    def _simple_parse(self, content: str) -> List[Dict]:
        """Парсинг календаря Yandex Calendar (HTML формат)"""
        events = []
        
        # Пробуем использовать BeautifulSoup для HTML парсинга
        if HAS_BS4:
            return self._parse_html_bs4(content)
        
        # Fallback на простой парсинг по строкам
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Ищем заголовки (начинаются с #)
            if line.startswith('# '):
                title = line[2:].strip()
                event = {
                    'title': title,
                    'start_date': None,
                    'end_date': None,
                    'description': '',
                    'author_uuids': [],
                    'tags': [],
                    'links': []
                }
                
                # Ищем дату в следующих строках (обычно следующая строка)
                for j in range(i + 1, min(i + 5, len(lines))):
                    date_line = lines[j].strip()
                    
                    # Парсим дату вида "6 декабря 2025 00:00 7 декабря 2025 00:00"
                    # или "6 декабря 2025 00:00"
                    date_patterns = [
                        r'(\d{1,2})\s+(\w+)\s+(\d{4})\s+(\d{2}:\d{2})',  # Полный формат
                        r'(\d{1,2})\s+(\w+)\s+(\d{4})',  # Без времени
                    ]
                    
                    for pattern in date_patterns:
                        date_match = re.search(pattern, date_line)
                        if date_match:
                            day, month_ru, year = date_match.groups()[:3]
                            time_str = date_match.group(4) if len(date_match.groups()) > 3 else "00:00"
                            
                            try:
                                # Преобразуем русские месяцы
                                months_ru = {
                                    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
                                    'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
                                    'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
                                    'январь': 1, 'февраль': 2, 'март': 3, 'апрель': 4,
                                    'май': 5, 'июнь': 6, 'июль': 7, 'август': 8,
                                    'сентябрь': 9, 'октябрь': 10, 'ноябрь': 11, 'декабрь': 12
                                }
                                month = months_ru.get(month_ru.lower())
                                if month:
                                    hour, minute = map(int, time_str.split(':'))
                                    event['start_date'] = datetime(int(year), month, int(day), hour, minute)
                                    break
                            except (ValueError, KeyError) as e:
                                logger.warning(f"Ошибка парсинга даты '{date_line}': {e}")
                    
                    if event['start_date']:
                        break
                
                # Ищем ссылки и описание в следующих строках
                description_lines = []
                for j in range(i + 1, min(i + 15, len(lines))):
                    link_line = lines[j]
                    
                    # Ищем ссылки на example.com
                    if 'example.com' in link_line:
                        # Извлекаем все URL из строки
                        urls = re.findall(r'https?://[^\s<>"\)]+', link_line)
                        for url in urls:
                            if url not in event['links']:
                                event['links'].append(url)
                            
                            # Извлекаем параметры из URL
                            try:
                                parsed_url = urlparse(url)
                                query_params = parse_qs(parsed_url.query)
                                
                                if 'authors' in query_params:
                                    event['author_uuids'].extend(query_params['authors'])
                                if 'tags' in query_params:
                                    event['tags'].extend(query_params['tags'])
                                
                                # Также проверяем slug в пути
                                path_parts = parsed_url.path.strip('/').split('/')
                                if len(path_parts) > 1 and path_parts[0] == 'catalog':
                                    # Может быть slug книги или коллекции
                                    pass
                            except Exception as e:
                                logger.warning(f"Ошибка парсинга URL '{url}': {e}")
                    
                    # Собираем описание (текст между заголовком и следующей секцией)
                    elif link_line.strip() and not link_line.strip().startswith('#'):
                        # Пропускаем строки с датами
                        if not re.search(r'\d{1,2}\s+\w+\s+\d{4}', link_line):
                            desc_text = link_line.strip()
                            if desc_text and desc_text not in description_lines:
                                description_lines.append(desc_text)
                    
                    # Останавливаемся на следующем заголовке
                    if j < len(lines) - 1 and lines[j + 1].strip().startswith('# '):
                        break
                
                # Формируем описание
                if description_lines:
                    event['description'] = '\n'.join(description_lines[:3])  # Максимум 3 строки
                
                events.append(event)
            i += 1
        
        logger.info(f"Распарсено событий: {len(events)}")
        return events
    
    def _parse_html_bs4(self, html_content: str) -> List[Dict]:
        """Парсинг HTML календаря с помощью BeautifulSoup"""
        events = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Находим все события (div с классом b-content-event)
            event_divs = soup.find_all('div', class_='b-content-event')
            
            for event_div in event_divs:
                event = {
                    'title': '',
                    'start_date': None,
                    'end_date': None,
                    'description': '',
                    'author_uuids': [],
                    'tags': [],
                    'links': []
                }
                
                # Заголовок события (h1)
                h1 = event_div.find('h1')
                if h1:
                    event['title'] = h1.get_text(strip=True)
                
                # Дата (div с классом e-time)
                time_div = event_div.find('div', class_='e-time')
                if time_div:
                    time_spans = time_div.find_all('span')
                    if time_spans and len(time_spans) >= 1:
                        date_str = time_spans[0].get_text(strip=True)
                        # Парсим дату вида "6 декабря 2025 00:00"
                        event['start_date'] = self._parse_date_string(date_str)
                
                # Описание (div с классом e-description)
                desc_div = event_div.find('div', class_='e-description')
                if desc_div:
                    # Текст описания
                    desc_text = desc_div.get_text(strip=True)
                    if desc_text:
                        event['description'] = desc_text
                    
                    # Ссылки
                    links = desc_div.find_all('a', href=True)
                    for link in links:
                        url = link.get('href', '')
                        if url:
                            event['links'].append(url)
                            
                            # Извлекаем UUID авторов из ссылок
                            parsed_url = urlparse(url)
                            query_params = parse_qs(parsed_url.query)
                            
                            if 'authors' in query_params:
                                event['author_uuids'].extend(query_params['authors'])
                            if 'tags' in query_params:
                                event['tags'].extend(query_params['tags'])
                
                if event['title']:
                    events.append(event)
            
            logger.info(f"Распарсено событий через BeautifulSoup: {len(events)}")
            
        except Exception as e:
            logger.error(f"Ошибка парсинга HTML: {e}")
            # Fallback на простой парсинг
            return self._parse_html_simple(html_content)
        
        return events
    
    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """Парсит строку даты вида '6 декабря 2025 00:00'"""
        try:
            # Парсим формат "6 декабря 2025 00:00"
            months_ru = {
                'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
                'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
                'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
                'январь': 1, 'февраль': 2, 'март': 3, 'апрель': 4,
                'май': 5, 'июнь': 6, 'июль': 7, 'август': 8,
                'сентябрь': 9, 'октябрь': 10, 'ноябрь': 11, 'декабрь': 12
            }
            
            # Паттерн: "6 декабря 2025 00:00"
            match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})\s+(\d{2}):(\d{2})', date_str)
            if match:
                day, month_ru, year, hour, minute = match.groups()
                month = months_ru.get(month_ru.lower())
                if month:
                    return datetime(int(year), month, int(day), int(hour), int(minute))
            
            # Пробуем без времени: "6 декабря 2025"
            match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date_str)
            if match:
                day, month_ru, year = match.groups()
                month = months_ru.get(month_ru.lower())
                if month:
                    return datetime(int(year), month, int(day), 0, 0)
            
        except Exception as e:
            logger.warning(f"Ошибка парсинга даты '{date_str}': {e}")
        
        return None
    
    def _parse_html_simple(self, html_content: str) -> List[Dict]:
        """Простой парсинг HTML без BeautifulSoup (fallback)"""
        events = []
        
        # Ищем события по паттерну <h1>...</h1>
        h1_pattern = r'<h1>(.*?)</h1>'
        time_pattern = r'<span>(\d{1,2}\s+\w+\s+\d{4}\s+\d{2}:\d{2})</span>'
        link_pattern = r'href="([^"]+)"'
        
        # Разбиваем на события по div.b-content-event
        event_blocks = re.split(r'<div class="b-content-event">', html_content)
        
        for block in event_blocks[1:]:  # Пропускаем первый пустой блок
            event = {
                'title': '',
                'start_date': None,
                'end_date': None,
                'description': '',
                'author_uuids': [],
                'tags': [],
                'links': []
            }
            
            # Заголовок
            h1_match = re.search(h1_pattern, block)
            if h1_match:
                event['title'] = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
            
            # Дата
            time_match = re.search(time_pattern, block)
            if time_match:
                date_str = time_match.group(1)
                event['start_date'] = self._parse_date_string(date_str)
            
            # Ссылки
            links = re.findall(link_pattern, block)
            for url in links:
                if 'example.com' in url:
                    event['links'].append(url)
                    parsed_url = urlparse(url)
                    query_params = parse_qs(parsed_url.query)
                    if 'authors' in query_params:
                        event['author_uuids'].extend(query_params['authors'])
                    if 'tags' in query_params:
                        event['tags'].extend(query_params['tags'])
            
            if event['title']:
                events.append(event)
        
        logger.info(f"Распарсено событий простым парсером: {len(events)}")
        return events
    
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
    
    async def get_books_by_tag(self, tag: str) -> List[Dict]:
        """Получает книги по тегу через GraphQL API"""
        query = """
        query GetBooksByTag($tagSlug: String!) {
          books(body: {
            isActive: true
            limit: 5
          }) {
            uuid
            name
            slug
          }
          tags(body: {
            slugs: [$tagSlug]
          }) {
            uuid
            name
            books(limit: 5) {
              uuid
              name
              slug
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
                        # Пробуем получить из tags
                        if 'tags' in data['data'] and data['data']['tags']:
                            tag_data = data['data']['tags'][0]
                            if 'books' in tag_data:
                                return tag_data['books']
        except Exception as e:
            logger.error(f"Ошибка запроса к API по тегу: {e}")
        
        return []
    
    def format_event_message(self, event: Dict, books: List[Dict] = None) -> str:
        """Форматирует сообщение о событии"""
        message_parts = []
        
        # Заголовок
        message_parts.append(f"📚 <b>{event['title']}</b>\n")
        
        # Дата
        if event['start_date']:
            date_str = event['start_date'].strftime("%d %B %Y")
            message_parts.append(f"📅 {date_str}\n")
        
        # Описание
        if event['description']:
            desc = event['description'][:200]  # Ограничиваем длину
            message_parts.append(f"{desc}\n")
        
        # Книги
        if books:
            message_parts.append("\n📖 <b>Книги в приложении «Свет»:</b>")
            for book in books[:5]:  # Максимум 5 книг
                book_name = book.get('name', 'Без названия')
                book_slug = book.get('slug', '')
                if book_slug:
                    book_url = f"https://example.com/catalog/{book_slug}"
                    message_parts.append(f"• <a href='{book_url}'>{book_name}</a>")
                else:
                    message_parts.append(f"• {book_name}")
        
        # Ссылки из календаря
        if event['links']:
            message_parts.append("\n🔗 <b>Ссылки:</b>")
            for link in event['links'][:3]:  # Максимум 3 ссылки
                message_parts.append(f"<a href='{link}'>Открыть в каталоге</a>")
        
        return "\n".join(message_parts)
    
    async def get_today_events(self) -> List[Dict]:
        """Получает события на сегодня из базы данных"""
        try:
            from database import EventDatabase
            db = EventDatabase()
            
            today = datetime.now()
            db_events = db.get_events_by_date(today)
            
            # Преобразуем формат для совместимости с ботом
            today_events = []
            for db_event in db_events:
                event = {
                    'title': db_event['title'],
                    'description': db_event['description'] or '',
                    'start_date': datetime.combine(db_event['event_date'], datetime.min.time()),
                    'author_uuids': [],
                    'tags': [],
                    'links': []
                }
                
                # Добавляем ссылку на автора/тег/категорию
                if db_event['reference_uuid']:
                    if db_event['event_type'] == 'author':
                        event['author_uuids'].append(db_event['reference_uuid'])
                        # Создаем ссылку на книги автора
                        event['links'].append(
                            f"https://example.com/catalog?authors={db_event['reference_uuid']}&page=1"
                        )
                    elif db_event['event_type'] == 'tag':
                        event['tags'].append(db_event['reference_uuid'])
                        event['links'].append(
                            f"https://example.com/catalog?tags={db_event['reference_uuid']}&page=1"
                        )
                    elif db_event['event_type'] == 'category':
                        event['links'].append(
                            f"https://example.com/catalog?categories={db_event['reference_uuid']}&page=1"
                        )
                
                today_events.append(event)
            
            logger.info(f"Найдено событий на сегодня из БД: {len(today_events)}")
            return today_events
            
        except ImportError:
            # Fallback на Яндекс календарь, если БД не доступна
            logger.warning("База данных не доступна, используем Яндекс календарь")
            xml_content = await self.fetch_calendar()
            all_events = self.parse_calendar(xml_content)
            
            today = datetime.now().date()
            today_events = []
            
            for event in all_events:
                if event['start_date']:
                    event_date = event['start_date'].date()
                    if event_date == today:
                        today_events.append(event)
            
            return today_events
    
    async def send_daily_digest(self):
        """Отправляет ежедневную рассылку"""
        try:
            events = await self.get_today_events()
            
            if not events:
                logger.info("Нет событий на сегодня")
                return
            
            # Отправляем каждое событие отдельным сообщением
            for event in events:
                books = []
                
                # Получаем книги по авторам
                for author_uuid in event['author_uuids']:
                    author_books = await self.get_books_by_author(author_uuid)
                    books.extend(author_books)
                
                # Получаем книги по тегам
                for tag in event['tags']:
                    tag_books = await self.get_books_by_tag(tag)
                    books.extend(tag_books)
                
                # Убираем дубликаты
                seen_uuids = set()
                unique_books = []
                for book in books:
                    uuid = book.get('uuid')
                    if uuid and uuid not in seen_uuids:
                        seen_uuids.add(uuid)
                        unique_books.append(book)
                
                # Форматируем и отправляем сообщение
                message = self.format_event_message(event, unique_books)
                
                try:
                    await self.bot.send_message(
                        chat_id=self.group_chat_id,
                        text=message,
                        parse_mode='HTML',
                        disable_web_page_preview=False
                    )
                    logger.info(f"Отправлено событие: {event['title']}")
                    
                    # Небольшая задержка между сообщениями
                    await asyncio.sleep(1)
                    
                except TelegramError as e:
                    logger.error(f"Ошибка отправки сообщения: {e}")
            
        except Exception as e:
            logger.error(f"Ошибка при отправке рассылки: {e}")
    
    async def run_daily(self):
        """Запускает бота в режиме ежедневной рассылки"""
        logger.info("Бот запущен в режиме ежедневной рассылки")
        
        while True:
            try:
                # Проверяем время (например, отправляем в 9:00)
                now = datetime.now()
                if now.hour == 9 and now.minute == 0:
                    await self.send_daily_digest()
                    # Ждем час, чтобы не отправить повторно
                    await asyncio.sleep(3600)
                else:
                    # Проверяем каждую минуту
                    await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Ошибка в цикле: {e}")
                await asyncio.sleep(60)


async def main():
    """Главная функция для запуска бота"""
    
    # ===== НАСТРОЙКИ =====
    # Получите токен бота у @BotFather в Telegram
    BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
    
    # URL календаря Yandex Calendar
    CALENDAR_URL = "https://calendar.yandex.ru/export/html.xml?private_token=<REDACTED>&tz_id=Europe/Moscow&limit=90"
    
    # URL GraphQL API (нужно узнать у администраторов API)
    GRAPHQL_ENDPOINT = "https://your-api-endpoint.com/graphql"
    
    # ID группы в Telegram (можно получить, добавив бота @userinfobot в группу)
    GROUP_CHAT_ID = "YOUR_GROUP_CHAT_ID"
    # ======================
    
    bot = LiteraryCalendarBot(
        bot_token=BOT_TOKEN,
        calendar_url=CALENDAR_URL,
        graphql_endpoint=GRAPHQL_ENDPOINT,
        group_chat_id=GROUP_CHAT_ID
    )
    
    # Запускаем ежедневную рассылку
    await bot.run_daily()


if __name__ == "__main__":
    asyncio.run(main())

