"""
Скрипт для запуска бота литературного календаря
Используйте этот файл для запуска бота
"""

import asyncio
import logging
import os
from literary_calendar_bot import LiteraryCalendarBot

# Поддержка переменных окружения (для деплоя)
# Используем переменные окружения, если они есть, иначе конфиг файл
BOT_TOKEN = os.getenv('BOT_TOKEN')
GRAPHQL_ENDPOINT = os.getenv('GRAPHQL_ENDPOINT')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')
CALENDAR_URL = os.getenv('CALENDAR_URL')

# Если переменные окружения не заданы, используем конфиг файл
if not all([BOT_TOKEN, GRAPHQL_ENDPOINT, GROUP_CHAT_ID]):
    try:
        import literary_calendar_bot_config as config
        BOT_TOKEN = BOT_TOKEN or config.BOT_TOKEN
        GRAPHQL_ENDPOINT = GRAPHQL_ENDPOINT or config.GRAPHQL_ENDPOINT
        GROUP_CHAT_ID = GROUP_CHAT_ID or config.GROUP_CHAT_ID
        CALENDAR_URL = CALENDAR_URL or config.CALENDAR_URL
    except ImportError:
        print("❌ Ошибка: Необходимо настроить переменные окружения или создать конфиг файл!")
        print("   Переменные окружения: BOT_TOKEN, GRAPHQL_ENDPOINT, GROUP_CHAT_ID, CALENDAR_URL")
        print("   Или создайте файл literary_calendar_bot_config.py")
        exit(1)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    
    # Проверяем конфигурацию
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        print("❌ Ошибка: Не настроен BOT_TOKEN!")
        print("   Получите токен у @BotFather в Telegram")
        print("   Установите переменную окружения: export BOT_TOKEN='ваш_токен'")
        return
    
    if GRAPHQL_ENDPOINT == "https://your-api-endpoint.com/graphql" or not GRAPHQL_ENDPOINT:
        print("❌ Ошибка: Не настроен GRAPHQL_ENDPOINT!")
        print("   Узнайте URL API у администраторов")
        print("   Установите переменную окружения: export GRAPHQL_ENDPOINT='ваш_api_url'")
        return
    
    if GROUP_CHAT_ID == "YOUR_GROUP_CHAT_ID" or not GROUP_CHAT_ID:
        print("❌ Ошибка: Не настроен GROUP_CHAT_ID!")
        print("   Узнайте ID группы через @userinfobot")
        print("   Установите переменную окружения: export GROUP_CHAT_ID='id_группы'")
        return
    
    # Устанавливаем дефолтный URL календаря, если не задан
    if not CALENDAR_URL:
        CALENDAR_URL = "https://calendar.yandex.ru/export/html.xml?private_token=<REDACTED>&tz_id=Europe/Moscow&limit=90"
    
    # Создаем бота
    bot = LiteraryCalendarBot(
        bot_token=BOT_TOKEN,
        calendar_url=CALENDAR_URL,
        graphql_endpoint=GRAPHQL_ENDPOINT,
        group_chat_id=GROUP_CHAT_ID
    )
    
    print("✅ Бот инициализирован")
    print(f"📅 Календарь: {CALENDAR_URL[:50]}...")
    print(f"🔗 API: {GRAPHQL_ENDPOINT}")
    print(f"👥 Группа: {GROUP_CHAT_ID}")
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

