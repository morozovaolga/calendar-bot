"""
Конфигурационный файл для бота литературного календаря
Замените значения на реальные при использовании
"""

# Токен Telegram бота (получите у @BotFather)
# Установите через переменную окружения: export BOT_TOKEN='...' (Linux/macOS) или $env:BOT_TOKEN='...' (PowerShell)
import os
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# URL GraphQL API (если требуется)
GRAPHQL_ENDPOINT = os.getenv('GRAPHQL_ENDPOINT', '')

# URL календаря (если требуется)
CALENDAR_URL = os.getenv('CALENDAR_URL', '')

DB_PATH = os.getenv('DB_PATH', 'literary_events.db')

# Время отправки ежедневного дайджеста (в часах, по умолчанию 13:00)
SEND_HOUR = int(os.getenv('SEND_HOUR', '13'))

# Часовой пояс
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Moscow')

# Максимальное количество книг в одном сообщении
MAX_BOOKS_PER_EVENT = 6

# Задержка между сообщениями (в секундах)
MESSAGE_DELAY = 1

# Логирование
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR