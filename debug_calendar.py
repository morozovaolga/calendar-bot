"""
Отладочный скрипт для проверки парсинга календаря и событий на сегодня
"""

import asyncio
import httpx
from datetime import datetime
from literary_calendar_bot import LiteraryCalendarBot

async def debug_calendar():
    """Отладка парсинга календаря"""
    
    calendar_url = "https://calendar.yandex.ru/export/html.xml?private_token=<REDACTED>&tz_id=Europe/Moscow&limit=90"
    
    bot = LiteraryCalendarBot(
        bot_token="dummy",
        calendar_url=calendar_url,
        graphql_endpoint="dummy",
        group_chat_id="dummy"
    )
    
    print("=" * 60)
    print("🔍 ОТЛАДКА ПАРСИНГА КАЛЕНДАРЯ")
    print("=" * 60)
    
    # Загружаем календарь
    print("\n1️⃣ Загрузка календаря...")
    xml_content = await bot.fetch_calendar()
    print(f"✅ Календарь загружен ({len(xml_content)} символов)")
    
    # Парсим события
    print("\n2️⃣ Парсинг событий...")
    all_events = bot.parse_calendar(xml_content)
    print(f"✅ Найдено всего событий: {len(all_events)}")
    
    # Показываем сегодняшнюю дату
    today = datetime.now().date()
    print(f"\n📅 Сегодняшняя дата: {today}")
    print(f"   Формат: {today.strftime('%d.%m.%Y')}")
    
    # Показываем все события с датами
    print("\n3️⃣ Все события с датами:")
    print("-" * 60)
    
    today_events = []
    for i, event in enumerate(all_events[:20], 1):  # Показываем первые 20
        if event['start_date']:
            event_date = event['start_date']
            event_date_only = event_date.date()
            is_today = event_date_only == today
            
            status = "✅ СЕГОДНЯ!" if is_today else "  "
            
            print(f"{status} {i}. {event['title'][:50]}")
            print(f"      Дата: {event_date.strftime('%d.%m.%Y %H:%M')}")
            print(f"      Только дата: {event_date_only}")
            print(f"      Совпадает с сегодня: {is_today}")
            
            if is_today:
                today_events.append(event)
        else:
            print(f"   {i}. {event['title'][:50]} - БЕЗ ДАТЫ")
    
    print("-" * 60)
    
    # Показываем события на сегодня
    print(f"\n4️⃣ События на сегодня ({today}):")
    if today_events:
        print(f"✅ Найдено событий на сегодня: {len(today_events)}")
        for event in today_events:
            print(f"\n📚 {event['title']}")
            print(f"   Дата: {event['start_date']}")
            print(f"   Авторы UUID: {event['author_uuids']}")
            print(f"   Ссылки: {len(event['links'])}")
    else:
        print("❌ Событий на сегодня не найдено!")
        
        # Показываем ближайшие события
        print("\n5️⃣ Ближайшие события (в пределах 7 дней):")
        from datetime import timedelta
        week_later = today + timedelta(days=7)
        
        upcoming = []
        for event in all_events:
            if event['start_date']:
                event_date = event['start_date'].date()
                if today <= event_date <= week_later:
                    upcoming.append((event_date, event))
        
        upcoming.sort(key=lambda x: x[0])
        
        for event_date, event in upcoming[:10]:
            days_diff = (event_date - today).days
            if days_diff == 0:
                print(f"   🎯 СЕГОДНЯ: {event['title'][:50]}")
            elif days_diff == 1:
                print(f"   📅 ЗАВТРА: {event['title'][:50]}")
            else:
                print(f"   📅 Через {days_diff} дней ({event_date}): {event['title'][:50]}")
    
    print("\n" + "=" * 60)
    print("✅ Отладка завершена")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(debug_calendar())

