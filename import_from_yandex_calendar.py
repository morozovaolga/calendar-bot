"""
Скрипт для импорта событий из Яндекс календаря в базу данных
"""

import asyncio
import httpx
import logging
from datetime import datetime
from database import EventDatabase
from literary_calendar_bot import LiteraryCalendarBot

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def import_from_yandex_calendar():
    """Импортирует события из Яндекс календаря в базу данных"""
    
    # URL календаря
    calendar_url = "https://calendar.yandex.ru/export/html.xml?private_token=1c7f766fab8185a98f934a458b51e7fe8ff5b636&tz_id=Europe/Moscow&limit=90"
    
    # Создаем временный бот для парсинга
    bot = LiteraryCalendarBot(
        bot_token="dummy",
        calendar_url=calendar_url,
        graphql_endpoint="dummy",
        group_chat_id="dummy"
    )
    
    # Инициализируем базу данных
    db = EventDatabase()
    
    print("=" * 60)
    print("🔄 ИМПОРТ СОБЫТИЙ ИЗ ЯНДЕКС КАЛЕНДАРЯ")
    print("=" * 60)
    
    # Загружаем календарь
    print("\n1️⃣ Загрузка календаря...")
    xml_content = await bot.fetch_calendar()
    print(f"✅ Календарь загружен ({len(xml_content)} символов)")
    
    # Парсим события
    print("\n2️⃣ Парсинг событий...")
    all_events = bot.parse_calendar(xml_content)
    print(f"✅ Найдено событий: {len(all_events)}")
    
    # Импортируем в базу данных
    print("\n3️⃣ Импорт в базу данных...")
    imported_count = 0
    skipped_count = 0
    error_count = 0
    
    for event in all_events:
        if not event.get('start_date'):
            skipped_count += 1
            logger.warning(f"Пропущено событие без даты: {event['title']}")
            continue
        
        try:
            # Определяем тип события и ссылки
            event_type = 'custom'
            reference_uuid = None
            reference_name = None
            
            # Если есть UUID авторов
            if event.get('author_uuids'):
                event_type = 'author'
                reference_uuid = event['author_uuids'][0]  # Берем первого автора
                # Попробуем найти имя автора из ссылок
                reference_name = None  # Можно будет добавить позже через API
            
            # Если есть теги
            elif event.get('tags'):
                event_type = 'tag'
                reference_uuid = event['tags'][0]  # Берем первый тег
                reference_name = None
            
            # Извлекаем название из ссылок, если есть
            if event.get('links'):
                for link in event['links']:
                    if 'authors=' in link:
                        # Уже обработали выше
                        pass
                    elif 'tags=' in link:
                        # Уже обработали выше
                        pass
            
            # Проверяем, не существует ли уже такое событие
            # Сравниваем по дате и названию
            event_date_only = event['start_date'].date()
            existing_events = db.get_events_by_date(event['start_date'])
            is_duplicate = False
            
            for existing in existing_events:
                # Сравниваем название (без учета регистра и пробелов)
                existing_title = existing['title'].strip().lower()
                new_title = event['title'].strip().lower()
                if existing_title == new_title:
                    is_duplicate = True
                    logger.debug(f"Дубликат найден: {event['title']}")
                    break
            
            if is_duplicate:
                skipped_count += 1
                continue
            
            # Добавляем событие
            event_id = db.add_event(
                title=event['title'],
                description=event.get('description', ''),
                event_date=event['start_date'],
                event_type=event_type,
                reference_uuid=reference_uuid,
                reference_name=reference_name
            )
            
            imported_count += 1
            date_str = event['start_date'].strftime('%d.%m.%Y') if event.get('start_date') else 'Без даты'
            print(f"  ✅ [{imported_count}] Импортировано: {event['title'][:50]} ({date_str})")
            
            # Показываем каждое 10-е событие для прогресса
            if imported_count % 10 == 0:
                print(f"     ... импортировано {imported_count} событий ...")
            
        except Exception as e:
            error_count += 1
            logger.error(f"Ошибка при импорте события '{event['title']}': {e}")
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ИМПОРТА")
    print("=" * 60)
    print(f"✅ Успешно импортировано: {imported_count}")
    print(f"⏭️  Пропущено (дубликаты/без даты): {skipped_count}")
    print(f"❌ Ошибок: {error_count}")
    print(f"📅 Всего обработано: {len(all_events)}")
    print("=" * 60)
    
    # Показываем примеры импортированных событий
    if imported_count > 0:
        print("\n📋 Примеры импортированных событий:")
        recent_events = db.get_all_events(limit=5)
        for i, evt in enumerate(recent_events[:5], 1):
            print(f"\n{i}. {evt['title']}")
            print(f"   Дата: {evt['event_date'].strftime('%d.%m.%Y')}")
            if evt['reference_name']:
                print(f"   Связано с: {evt['reference_name']}")
    
    print("\n✅ Импорт завершен!")
    print("\n💡 Теперь можно:")
    print("   1. Запустить веб-приложение: python web_app.py")
    print("   2. Просмотреть события: http://localhost:5000")
    print("   3. Добавить новые события через форму")


if __name__ == "__main__":
    asyncio.run(import_from_yandex_calendar())

