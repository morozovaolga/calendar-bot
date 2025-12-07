"""
Быстрый импорт всех событий из Яндекс календаря
Упрощенная версия с подробным выводом
"""

import asyncio
import httpx
from datetime import datetime
from database import EventDatabase
from literary_calendar_bot import LiteraryCalendarBot

async def quick_import():
    """Быстрый импорт с подробным выводом"""
    
    print("🚀 БЫСТРЫЙ ИМПОРТ СОБЫТИЙ")
    print("=" * 60)
    
    # Инициализация
    calendar_url = "https://calendar.yandex.ru/export/html.xml?private_token=1c7f766fab8185a98f934a458b51e7fe8ff5b636&tz_id=Europe/Moscow&limit=90"
    db = EventDatabase()
    
    bot = LiteraryCalendarBot(
        bot_token="dummy",
        calendar_url=calendar_url,
        graphql_endpoint="dummy",
        group_chat_id="dummy"
    )
    
    # Шаг 1: Загрузка
    print("\n📥 Загрузка календаря...")
    try:
        xml_content = await bot.fetch_calendar()
        print(f"✅ Загружено {len(xml_content)} символов")
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return
    
    # Шаг 2: Парсинг
    print("\n🔍 Парсинг событий...")
    try:
        events = bot.parse_calendar(xml_content)
        print(f"✅ Найдено {len(events)} событий")
    except Exception as e:
        print(f"❌ Ошибка парсинга: {e}")
        import traceback
        traceback.print_exc()
        return
    
    if not events:
        print("⚠️ События не найдены в календаре!")
        return
    
    # Шаг 3: Проверка базы
    print("\n📊 Проверка базы данных...")
    existing = db.get_all_events()
    print(f"   Событий в базе: {len(existing)}")
    
    # Шаг 4: Импорт
    print("\n💾 Импорт событий...")
    imported = 0
    skipped = 0
    errors = 0
    
    for i, event in enumerate(events, 1):
        # Пропускаем события без даты
        if not event.get('start_date'):
            skipped += 1
            print(f"  ⏭️  [{i}/{len(events)}] Пропущено (нет даты): {event['title'][:40]}")
            continue
        
        try:
            # Определяем тип
            event_type = 'custom'
            ref_uuid = None
            ref_name = None
            
            if event.get('author_uuids'):
                event_type = 'author'
                ref_uuid = event['author_uuids'][0]
            elif event.get('tags'):
                event_type = 'tag'
                ref_uuid = event['tags'][0]
            
            # Проверка дубликата
            event_date = event['start_date'].date()
            existing_today = db.get_events_by_date(event['start_date'])
            
            is_dup = any(
                e['title'].strip().lower() == event['title'].strip().lower()
                for e in existing_today
            )
            
            if is_dup:
                skipped += 1
                if i <= 5 or imported < 3:  # Показываем первые несколько
                    print(f"  ⏭️  [{i}/{len(events)}] Дубликат: {event['title'][:40]}")
                continue
            
            # Импорт
            db.add_event(
                title=event['title'],
                description=event.get('description', ''),
                event_date=event['start_date'],
                event_type=event_type,
                reference_uuid=ref_uuid,
                reference_name=ref_name
            )
            
            imported += 1
            date_str = event['start_date'].strftime('%d.%m.%Y')
            print(f"  ✅ [{i}/{len(events)}] {event['title'][:40]} ({date_str})")
            
        except Exception as e:
            errors += 1
            print(f"  ❌ [{i}/{len(events)}] Ошибка: {event['title'][:40]} - {e}")
    
    # Итоги
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ")
    print("=" * 60)
    print(f"✅ Импортировано: {imported}")
    print(f"⏭️  Пропущено: {skipped}")
    print(f"❌ Ошибок: {errors}")
    print(f"📅 Всего в календаре: {len(events)}")
    
    # Проверка результата
    final_count = len(db.get_all_events())
    print(f"\n💾 Событий в базе теперь: {final_count}")
    
    if imported > 0:
        print("\n✅ Импорт успешно завершен!")
        print("   Запустите веб-приложение: python web_app.py")
    else:
        print("\n⚠️ События не были импортированы.")
        print("   Возможные причины:")
        print("   - Все события уже есть в базе")
        print("   - События без дат")
        print("   - Ошибки при импорте")

if __name__ == "__main__":
    asyncio.run(quick_import())

