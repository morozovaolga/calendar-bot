"""
Простой скрипт для тестирования бота литературного календаря
Запустите этот файл для проверки работы перед настройкой полного бота
"""

import asyncio
import httpx
from literary_calendar_bot import LiteraryCalendarBot

async def test_calendar_parsing():
    """Тестирует парсинг календаря"""
    print("🔍 Тестирование парсинга календаря...")
    
    calendar_url = "https://calendar.yandex.ru/export/html.xml?private_token=<REDACTED>&tz_id=Europe/Moscow&limit=90"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(calendar_url)
        if response.status_code == 200:
            content = response.text
            print(f"✅ Календарь загружен ({len(content)} символов)")
            
            # Создаем временный бот для парсинга
            bot = LiteraryCalendarBot(
                bot_token="dummy",
                calendar_url=calendar_url,
                graphql_endpoint="dummy",
                group_chat_id="dummy"
            )
            
            events = bot.parse_calendar(content)
            print(f"✅ Найдено событий: {len(events)}")
            
            # Показываем первые 3 события
            for i, event in enumerate(events[:3], 1):
                print(f"\n📅 Событие {i}:")
                print(f"   Название: {event['title']}")
                print(f"   Дата: {event['start_date']}")
                print(f"   Авторы UUID: {event['author_uuids']}")
                print(f"   Теги: {event['tags']}")
                print(f"   Ссылки: {len(event['links'])}")
            
            return True
        else:
            print(f"❌ Ошибка загрузки: {response.status_code}")
            return False

async def test_today_events():
    """Тестирует получение событий на сегодня"""
    print("\n📅 Тестирование событий на сегодня...")
    
    calendar_url = "https://calendar.yandex.ru/export/html.xml?private_token=<REDACTED>&tz_id=Europe/Moscow&limit=90"
    
    bot = LiteraryCalendarBot(
        bot_token="dummy",
        calendar_url=calendar_url,
        graphql_endpoint="dummy",
        group_chat_id="dummy"
    )
    
    events = await bot.get_today_events()
    
    if events:
        print(f"✅ Найдено событий на сегодня: {len(events)}")
        for event in events:
            print(f"\n📚 {event['title']}")
            if event['start_date']:
                print(f"   Дата: {event['start_date']}")
            if event['author_uuids']:
                print(f"   Авторы: {event['author_uuids']}")
    else:
        print("ℹ️  Событий на сегодня нет")
    
    return events

async def test_message_formatting():
    """Тестирует форматирование сообщений"""
    print("\n💬 Тестирование форматирования сообщений...")
    
    bot = LiteraryCalendarBot(
        bot_token="dummy",
        calendar_url="dummy",
        graphql_endpoint="dummy",
        group_chat_id="dummy"
    )
    
    # Тестовое событие
    test_event = {
        'title': 'Антон Чехов родился в 1860 году',
        'start_date': None,
        'end_date': None,
        'description': 'Книги Чехова в приложении',
        'author_uuids': ['c52f926c-dde3-4631-b1cf-4a8849ad5be9'],
        'tags': [],
        'links': ['https://example.com/catalog?authors=c52f926c-dde3-4631-b1cf-4a8849ad5be9&page=1']
    }
    
    test_books = [
        {'uuid': '1', 'name': 'Вишневый сад', 'slug': 'vishnevyy-sad'},
        {'uuid': '2', 'name': 'Дама с собачкой', 'slug': 'dama-s-sobachkoy'}
    ]
    
    message = bot.format_event_message(test_event, test_books)
    print("✅ Сообщение сформировано:")
    print("\n" + "="*50)
    print(message)
    print("="*50)

async def main():
    """Запускает все тесты"""
    print("🧪 Тестирование бота литературного календаря\n")
    
    # Тест 1: Парсинг календаря
    await test_calendar_parsing()
    
    # Тест 2: События на сегодня
    await test_today_events()
    
    # Тест 3: Форматирование сообщений
    await test_message_formatting()
    
    print("\n✅ Тестирование завершено!")
    print("\n📝 Следующие шаги:")
    print("1. Получите токен бота у @BotFather")
    print("2. Узнайте ID группы (используйте @userinfobot)")
    print("3. Узнайте URL GraphQL API")
    print("4. Заполните literary_calendar_bot_config.py")
    print("5. Запустите literary_calendar_bot.py")

if __name__ == "__main__":
    asyncio.run(main())

