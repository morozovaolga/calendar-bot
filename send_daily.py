"""
Скрипт для отправки ежедневной рассылки
Можно запускать из командной строки или через cron/GitHub Actions
"""

import asyncio
import logging
import os
import sys
from literary_calendar_bot import LiteraryCalendarBot

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция отправки рассылки"""
    
    # Получаем переменные окружения
    bot_token = os.getenv('BOT_TOKEN')
    graphql_endpoint = os.getenv('GRAPHQL_ENDPOINT')
    group_chat_id = os.getenv('GROUP_CHAT_ID')
    calendar_url = os.getenv('CALENDAR_URL')
    
    # Проверяем наличие всех переменных
    if not all([bot_token, graphql_endpoint, group_chat_id]):
        logger.error("❌ Отсутствуют необходимые переменные окружения!")
        logger.error("Требуются: BOT_TOKEN, GRAPHQL_ENDPOINT, GROUP_CHAT_ID")
        sys.exit(1)
    
    # Устанавливаем дефолтный URL календаря, если не задан
    if not calendar_url:
        calendar_url = "https://calendar.yandex.ru/export/html.xml?private_token=1c7f766fab8185a98f934a458b51e7fe8ff5b636&tz_id=Europe/Moscow&limit=90"
        logger.info("Используется дефолтный URL календаря")
    
    logger.info("🚀 Запуск отправки ежедневной рассылки...")
    logger.info(f"📅 Календарь: {calendar_url[:50]}...")
    logger.info(f"🔗 API: {graphql_endpoint}")
    logger.info(f"👥 Группа: {group_chat_id}")
    
    try:
        # Создаем бота
        bot = LiteraryCalendarBot(
            bot_token=bot_token,
            calendar_url=calendar_url,
            graphql_endpoint=graphql_endpoint,
            group_chat_id=group_chat_id
        )
        
        # Отправляем рассылку
        await bot.send_daily_digest()
        
        logger.info("✅ Ежедневная рассылка успешно отправлена!")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке рассылки: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

