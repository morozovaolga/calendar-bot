"""
Отладочный скрипт для проверки импорта событий
"""

import asyncio
import httpx
from datetime import datetime
from database import EventDatabase
from literary_calendar_bot import LiteraryCalendarBot

async def debug_import():
    """Отладка импорта событий"""
    
    print("=" * 60)
    print("🔍 ОТЛАДКА ИМПОРТА СОБЫТИЙ")
    print("=" * 60)
    
    # 1. Проверяем базу данных
    print("\n1️⃣ Проверка базы данных...")
    db = EventDatabase()
    db_events = db.get_all_events(limit=100)
    print(f"✅ Событий в базе данных: {len(db_events)}")
    
    if db_events:
        print("\nСобытия в базе:")
        for i, event in enumerate(db_events[:10], 1):
            print(f"  {i}. {event['title']} - {event['event_date']}")
    else:
        print("  ⚠️ База данных пуста")
    
    # 2. Проверяем календарь
    print("\n2️⃣ Проверка Яндекс календаря...")
    calendar_url = "https://calendar.yandex.ru/export/html.xml?private_token=1c7f766fab8185a98f934a458b51e7fe8ff5b636&tz_id=Europe/Moscow&limit=90"
    
    bot = LiteraryCalendarBot(
        bot_token="dummy",
        calendar_url=calendar_url,
        graphql_endpoint="dummy",
        group_chat_id="dummy"
    )
    
    try:
        xml_content = await bot.fetch_calendar()
        print(f"✅ Календарь загружен ({len(xml_content)} символов)")
        
        # Парсим события
        print("\n3️⃣ Парсинг событий из календаря...")
        calendar_events = bot.parse_calendar(xml_content)
        print(f"✅ Найдено событий в календаре: {len(calendar_events)}")
        
        if calendar_events:
            print("\nПервые 10 событий из календаря:")
            for i, event in enumerate(calendar_events[:10], 1):
                date_str = event['start_date'].strftime('%d.%m.%Y') if event.get('start_date') else 'Без даты'
                print(f"  {i}. {event['title'][:50]}")
                print(f"     Дата: {date_str}")
                print(f"     Авторы UUID: {event.get('author_uuids', [])}")
                print(f"     Ссылки: {len(event.get('links', []))}")
        else:
            print("  ⚠️ События не найдены в календаре")
        
        # 3. Проверяем, какие события уже есть в базе
        print("\n4️⃣ Сравнение с базой данных...")
        
        calendar_dates = {}
        for event in calendar_events:
            if event.get('start_date'):
                date_key = event['start_date'].date()
                title = event['title']
                calendar_dates[(date_key, title)] = event
        
        db_dates = {}
        for event in db_events:
            date_key = event['event_date']
            title = event['title']
            db_dates[(date_key, title)] = event
        
        print(f"  Событий в календаре: {len(calendar_dates)}")
        print(f"  Событий в базе: {len(db_dates)}")
        
        # Находим события, которых нет в базе
        missing_events = []
        for key, event in calendar_dates.items():
            if key not in db_dates:
                missing_events.append(event)
        
        print(f"\n  📋 Событий для импорта: {len(missing_events)}")
        
        if missing_events:
            print("\n  Примеры событий, которых нет в базе:")
            for i, event in enumerate(missing_events[:5], 1):
                date_str = event['start_date'].strftime('%d.%m.%Y') if event.get('start_date') else 'Без даты'
                print(f"    {i}. {event['title'][:50]} ({date_str})")
        
        # 4. Пробуем импортировать одно событие
        if missing_events:
            print("\n5️⃣ Тестовый импорт одного события...")
            test_event = missing_events[0]
            
            try:
                event_type = 'custom'
                reference_uuid = None
                reference_name = None
                
                if test_event.get('author_uuids'):
                    event_type = 'author'
                    reference_uuid = test_event['author_uuids'][0]
                
                event_id = db.add_event(
                    title=test_event['title'],
                    description=test_event.get('description', ''),
                    event_date=test_event['start_date'],
                    event_type=event_type,
                    reference_uuid=reference_uuid,
                    reference_name=reference_name
                )
                
                print(f"  ✅ Тестовое событие импортировано! ID: {event_id}")
                print(f"     Название: {test_event['title']}")
                
                # Проверяем, что оно появилось в базе
                new_events = db.get_all_events(limit=100)
                print(f"  ✅ Теперь событий в базе: {len(new_events)}")
                
            except Exception as e:
                print(f"  ❌ Ошибка при тестовом импорте: {e}")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Отладка завершена")
    print("=" * 60)
    
    print("\n💡 Рекомендации:")
    print("1. Если события в календаре найдены, но не импортируются:")
    print("   - Запустите: python import_from_yandex_calendar.py")
    print("2. Если события не парсятся из календаря:")
    print("   - Проверьте формат календаря")
    print("   - Запустите: python debug_calendar.py")
    print("3. Если база данных пуста:")
    print("   - Проверьте права на запись файла")
    print("   - Убедитесь, что файл literary_events.db создан")

if __name__ == "__main__":
    asyncio.run(debug_import())

