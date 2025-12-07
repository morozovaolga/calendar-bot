"""
Скрипт для запуска бота литературного календаря
Используйте этот файл для запуска бота
"""

import asyncio
import logging
import os
from literary_calendar_bot import LiteraryCalendarBot

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    
    # Загрузка конфигурации внутри функции для избежания проблем с областью видимости
    bot_token = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    graphql_endpoint = os.getenv('GRAPHQL_ENDPOINT', 'https://api.svetapp.rusneb.ru/graphql')
    group_chat_id = os.getenv('GROUP_CHAT_ID', 'YOUR_GROUP_CHAT_ID')
    calendar_url = os.getenv('CALENDAR_URL', 'https://calendar.yandex.ru/export/html.xml?private_token=1c7f766fab8185a98f934a458b51e7fe8ff5b636&tz_id=Europe/Moscow&limit=90')
    timezone = os.getenv('TIMEZONE', 'Europe/Moscow')
    send_hour = int(os.getenv('SEND_HOUR', '9'))

    # Если хотя бы один из основных параметров - placeholder, пробуем загрузить из конфига
    if "YOUR_BOT_TOKEN_HERE" in bot_token or "YOUR_GROUP_CHAT_ID" in group_chat_id:
        try:
            import literary_calendar_bot_config as config
            bot_token = getattr(config, 'BOT_TOKEN', bot_token)
            graphql_endpoint = getattr(config, 'GRAPHQL_ENDPOINT', graphql_endpoint)
            group_chat_id = getattr(config, 'GROUP_CHAT_ID', group_chat_id)
            calendar_url = getattr(config, 'CALENDAR_URL', calendar_url)
            timezone = getattr(config, 'TIMEZONE', timezone)
            send_hour = getattr(config, 'SEND_HOUR', send_hour)
        except ImportError:
            pass  # Конфиг файл не обязателен, используем переменные окружения или placeholder'ы

    # Проверяем конфигурацию
    if not bot_token or "YOUR_BOT_TOKEN_HERE" in bot_token:
        print("⚠️  Предупреждение: BOT_TOKEN не настроен!")
        print("   Получите токен у @BotFather в Telegram")
        print("   Установите переменную окружения: export BOT_TOKEN='ваш_токен'")
        print("   Или измените значение в файле literary_calendar_bot_config.py")
        # return  # Закомментировано для возможности запуска тестов
    
    if not graphql_endpoint or "https://your-api-endpoint.com/graphql" in graphql_endpoint:
        print("⚠️  Предупреждение: GRAPHQL_ENDPOINT не настроен!")
        print("   Узнайте URL API у администраторов")
        print("   Установите переменную окружения: export GRAPHQL_ENDPOINT='ваш_api_url'")
        print("   Или измените значение в файле literary_calendar_bot_config.py")
        # return  # Закомментировано для возможности запуска тестов
    
    if not group_chat_id or "YOUR_GROUP_CHAT_ID" in group_chat_id:
        print("⚠️  Предупреждение: GROUP_CHAT_ID не настроен!")
        print("   Узнайте ID группы через @userinfobot")
        print("   Установите переменную окружения: export GROUP_CHAT_ID='id_группы'")
        print("   Или измените значение в файле literary_calendar_bot_config.py")
        # return  # Закомментировано для возможности запуска тестов
    
    # Устанавливаем дефолтный URL календаря, если не задан
    if not calendar_url:
        calendar_url = "https://calendar.yandex.ru/export/html.xml?private_token=1c7f766fab8185a98f934a458b51e7fe8ff5b636&tz_id=Europe/Moscow&limit=90"
    
    # Создаем бота
    bot = LiteraryCalendarBot(
        bot_token=bot_token,
        calendar_url=calendar_url,
        graphql_endpoint=graphql_endpoint,
        group_chat_id=group_chat_id,
        timezone=timezone,
        send_hour=send_hour
    )
    
    print("✅ Бот инициализирован")
    print(f"📅 Календарь: {calendar_url[:50]}...")
    print(f"🔗 API: {graphql_endpoint}")
    print(f"👥 Группа: {group_chat_id}")
    print("\n" + "="*50)
    print("Выберите режим работы:")
    print("1. Отправить события на сегодня (тест)")
    print("2. Запустить ежедневную рассылку")
    print("="*50)
    
    # Для автоматического запуска раскомментируйте нужную строку:
    
    # Режим 1: Тестовая отправка
    print("\n🧪 Тестовый режим: отправка событий на сегодня...")
    await bot.send_daily_digest()
    print("✅ Тестовая отправка завершена")
    
    # Режим 2: Ежедневная рассылка (для продакшена)
    # Для автоматического запуска в продакшене раскомментируйте:
    print("\n⏰ Режим ежедневной рассылки запущен")
    print("Бот будет проверять календарь каждый день в 9:00")
    await bot.run_daily()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        print(f"\n❌ Ошибка: {e}")
        print("Проверьте логи выше для деталей")

