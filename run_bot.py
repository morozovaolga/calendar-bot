"""
Скрипт для запуска бота литературного календаря
Используйте этот файл для запуска бота с поддержкой команд
"""

import asyncio
import logging
import os
from literary_calendar_bot import LiteraryCalendarBot
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class BotWithCommands:
    def __init__(self, bot_token: str, calendar_url: str, graphql_endpoint: str, group_chat_id: str, timezone: str = "Europe/Moscow", send_hour: int = 9):
        self.literary_bot = LiteraryCalendarBot(
            bot_token=bot_token,
            calendar_url=calendar_url,
            graphql_endpoint=graphql_endpoint,
            group_chat_id=group_chat_id,
            timezone=timezone,
            send_hour=send_hour
        )
        self.app = Application.builder().token(bot_token).build()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        await update.message.reply_text(
            "Привет! Я бот литературного календаря. Используйте команду /send_events для получения событий на сегодня."
        )

    async def send_events_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /send_events - отправляет события в личный чат"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Отправляем события в личный чат пользователя
        await self.literary_bot.send_daily_digest(chat_id=chat_id)
        
        logger.info(f"Команда send_events выполнена для пользователя {user_id} в чате {chat_id}")

    async def setup_handlers(self):
        """Настройка обработчиков команд"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("send_events", self.send_events_command))

    async def run_polling(self):
        """Запуск бота в режиме polling"""
        await self.setup_handlers()
        await self.app.initialize()
        await self.app.start()
        print("🤖 Бот запущен в режиме polling")
        print("Отправьте команду /start или /send_events в Telegram")
        await self.app.updater.start_polling()
        await self.app.updater.idle()

    async def run_daily(self):
        """Запуск ежедневной рассылки"""
        await self.literary_bot.run_daily()


async def main():
    """Главная функция запуска бота"""
    
    # Загрузка конфигурации внутри функции для избежания проблем с областью видимости
    bot_token = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    graphql_endpoint = os.getenv('GRAPHQL_ENDPOINT', 'https://api.example.com/graphql')
    group_chat_id = os.getenv('GROUP_CHAT_ID', 'YOUR_GROUP_CHAT_ID')
    calendar_url = os.getenv('CALENDAR_URL', 'https://calendar.yandex.ru/export/html.xml?private_token=<REDACTED>&tz_id=Europe/Moscow&limit=90')
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
        calendar_url = "https://calendar.yandex.ru/export/html.xml?private_token=<REDACTED>&tz_id=Europe/Moscow&limit=90"
    
    # Создаем бота с поддержкой команд
    bot_with_commands = BotWithCommands(
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
    print("1. Запустить бота с поддержкой команд")
    print("2. Запустить ежедневную рассылку")
    print("="*50)
    
    # Проверяем переменную окружения для автоматического выбора режима
    import sys
    mode = os.getenv('BOT_MODE', '')
    
    if mode == 'daily' or len(sys.argv) > 1 and sys.argv[1] == 'daily':
        choice = "2"
    elif mode == 'commands' or len(sys.argv) > 1 and sys.argv[1] == 'commands':
        choice = "1"
    else:
        try:
            choice = input("Введите номер режима (1 или 2, по умолчанию 1): ").strip()
        except EOFError:
            # Если ввод не интерактивен (например, в докере), используем режим команд
            choice = "1"
    
    if choice == "2":
        # Режим 2: Ежедневная рассылка
        print("\n⏰ Режим ежедневной рассылки запущен")
        print("Бот будет проверять календарь каждый день в 9:00")
        await bot_with_commands.run_daily()
    else:
        # Режим 1: Запуск бота с командами
        print("\n🤖 Режим бота с командами запущен")
        await bot_with_commands.run_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        print(f"\n❌ Ошибка: {e}")
        print("Проверьте логи выше для деталей")

