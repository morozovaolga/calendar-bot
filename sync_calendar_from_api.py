"""
Скрипт для автоматической синхронизации литературных дат
из GraphQL API в Яндекс Календарь

Этот скрипт:
1. Получает всех авторов из API
2. Извлекает даты рождения/смерти
3. Создает события в Яндекс Календаре
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional
import httpx

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class CalendarSync:
    """Синхронизация календаря с API"""
    
    def __init__(
        self,
        graphql_endpoint: str,
        yandex_calendar_token: Optional[str] = None,
        calendar_id: Optional[str] = None
    ):
        """
        Инициализация синхронизатора
        
        Args:
            graphql_endpoint: URL GraphQL API
            yandex_calendar_token: Токен Яндекс Календаря (опционально, для автоматического добавления)
            calendar_id: ID календаря в Яндекс (опционально)
        """
        self.graphql_endpoint = graphql_endpoint
        self.yandex_calendar_token = yandex_calendar_token
        self.calendar_id = calendar_id
    
    async def get_all_authors(self) -> List[Dict]:
        """Получает всех авторов из API"""
        query = """
        query GetAllAuthors {
          authors(body: {
            limit: 1000
            page: 1
          }) {
            uuid
            firstName
            lastName
            patronymic
            birthday
            deathday
            slug
            isActive
          }
        }
        """
        
        all_authors = []
        page = 1
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                while True:
                    query_with_page = query.replace('page: 1', f'page: {page}')
                    
                    response = await client.post(
                        self.graphql_endpoint,
                        json={"query": query_with_page},
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data and 'authors' in data['data']:
                            authors = data['data']['authors']
                            if not authors:
                                break
                            all_authors.extend(authors)
                            logger.info(f"Получено авторов со страницы {page}: {len(authors)}")
                            
                            # Если получили меньше чем limit, значит это последняя страница
                            if len(authors) < 1000:
                                break
                            page += 1
                        else:
                            logger.error(f"Ошибка API: {data}")
                            break
                    else:
                        logger.error(f"Ошибка HTTP: {response.status_code}")
                        break
        except Exception as e:
            logger.error(f"Ошибка получения авторов: {e}")
        
        logger.info(f"Всего получено авторов: {len(all_authors)}")
        return all_authors
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Парсит дату из строки
        Поддерживает форматы: "1905", "1905-01-01", "01.01.1905"
        """
        if not date_str:
            return None
        
        date_str = date_str.strip()
        
        # Только год
        if re.match(r'^\d{4}$', date_str):
            year = int(date_str)
            return datetime(year, 1, 1)
        
        # Полная дата в разных форматах
        formats = [
            '%Y-%m-%d',
            '%d.%m.%Y',
            '%d/%m/%Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logger.warning(f"Не удалось распарсить дату: {date_str}")
        return None
    
    def format_author_name(self, author: Dict) -> str:
        """Форматирует полное имя автора"""
        parts = []
        if author.get('lastName'):
            parts.append(author['lastName'])
        if author.get('firstName'):
            parts.append(author['firstName'])
        if author.get('patronymic'):
            parts.append(author['patronymic'])
        return ' '.join(parts) if parts else 'Неизвестный автор'
    
    def create_calendar_event(
        self,
        author: Dict,
        event_type: str,  # 'birthday' или 'deathday'
        date: datetime
    ) -> Dict:
        """
        Создает объект события для календаря
        
        Returns:
            Словарь с данными события в формате для экспорта
        """
        author_name = self.format_author_name(author)
        author_uuid = author.get('uuid', '')
        author_slug = author.get('slug', '')
        
        if event_type == 'birthday':
            title = f"{author_name} родился в {date.year} году"
            description = f"День рождения {author_name}"
        else:
            title = f"{author_name} умер в {date.year} году"
            description = f"День памяти {author_name}"
        
        # Создаем ссылку на книги автора
        if author_uuid:
            link = f"https://svetapp.rusneb.ru/catalog?authors={author_uuid}&page=1"
            description += f"\n\nКниги {author_name} в приложении «Свет»\n{link}"
        
        # Форматируем дату для календаря
        # Яндекс Календарь использует формат: "6 декабря 2025 00:00"
        months_ru = {
            1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
            5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
            9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
        }
        
        date_str = f"{date.day} {months_ru[date.month]} {date.year} 00:00"
        
        return {
            'title': title,
            'description': description,
            'date': date_str,
            'author_uuid': author_uuid,
            'author_name': author_name,
            'link': link if author_uuid else None
        }
    
    def generate_calendar_export(self, events: List[Dict]) -> str:
        """
        Генерирует текст календаря в формате для экспорта
        (формат, который использует Яндекс Календарь)
        """
        lines = []
        
        # Сортируем события по дате
        events_sorted = sorted(events, key=lambda x: x['date'])
        
        for event in events_sorted:
            lines.append(f"# {event['title']}")
            lines.append(event['date'])
            if event.get('link'):
                lines.append(event['link'])
            if event.get('description'):
                # Добавляем описание, если оно не слишком длинное
                desc = event['description'][:200]
                if desc:
                    lines.append(desc)
            lines.append("")  # Пустая строка между событиями
        
        return "\n".join(lines)
    
    async def sync_author_events(self) -> List[Dict]:
        """
        Синхронизирует события авторов из API
        
        Returns:
            Список событий для календаря
        """
        authors = await self.get_all_authors()
        events = []
        
        for author in authors:
            if not author.get('isActive', True):
                continue
            
            # Событие дня рождения
            if author.get('birthday'):
                birth_date = self.parse_date(author['birthday'])
                if birth_date:
                    # Создаем событие на каждый год (только день и месяц)
                    event = self.create_calendar_event(author, 'birthday', birth_date)
                    events.append(event)
            
            # Событие дня памяти (смерти)
            if author.get('deathday'):
                death_date = self.parse_date(author['deathday'])
                if death_date:
                    event = self.create_calendar_event(author, 'deathday', death_date)
                    events.append(event)
        
        logger.info(f"Создано событий: {len(events)}")
        return events
    
    def save_to_file(self, events: List[Dict], filename: str = "literary_calendar_export.txt"):
        """Сохраняет события в файл"""
        calendar_text = self.generate_calendar_export(events)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(calendar_text)
        
        logger.info(f"События сохранены в файл: {filename}")
        return filename


async def main():
    """Главная функция"""
    
    # ===== НАСТРОЙКИ =====
    GRAPHQL_ENDPOINT = "https://your-api-endpoint.com/graphql"
    OUTPUT_FILE = "literary_calendar_export.txt"
    # =====================
    
    sync = CalendarSync(
        graphql_endpoint=GRAPHQL_ENDPOINT,
        yandex_calendar_token=None,  # Пока не используем API Яндекс
        calendar_id=None
    )
    
    print("🔄 Начинаем синхронизацию календаря...")
    print(f"📡 Подключение к API: {GRAPHQL_ENDPOINT}")
    
    # Получаем события из API
    events = await sync.sync_author_events()
    
    if not events:
        print("❌ События не найдены. Проверьте подключение к API.")
        return
    
    print(f"✅ Найдено событий: {len(events)}")
    
    # Сохраняем в файл
    filename = sync.save_to_file(events, OUTPUT_FILE)
    
    print(f"\n📄 События сохранены в файл: {filename}")
    print("\n📝 Следующие шаги:")
    print("1. Откройте Яндекс Календарь: https://calendar.yandex.ru")
    print("2. Создайте новый календарь 'Литературные даты'")
    print("3. Импортируйте события из файла (или добавьте вручную)")
    print("4. Скопируйте URL экспорта календаря")
    print("5. Используйте этот URL в настройках бота")
    
    # Показываем примеры событий
    print("\n📅 Примеры событий (первые 5):")
    for i, event in enumerate(events[:5], 1):
        print(f"\n{i}. {event['title']}")
        print(f"   Дата: {event['date']}")
        if event.get('link'):
            print(f"   Ссылка: {event['link']}")


if __name__ == "__main__":
    asyncio.run(main())

