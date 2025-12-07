"""
Конфигурационный файл для бота литературного календаря
Замените значения на реальные при использовании
"""

# Токен Telegram бота (получите у @BotFather)
BOT_TOKEN = "8470133642:AAHj5TBjRMDEtjGSCvwGpJot2vEUC_YEV-c"

# URL GraphQL API сервиса "Свет"
GRAPHQL_ENDPOINT = "https://svetapp-test.rusneb.ru/graphql"

# ID группы в Telegram (можно получить через @userinfobot)
GROUP_CHAT_ID = "5016711578"

# URL календаря Yandex Calendar (если используется)
CALENDAR_URL = "https://calendar.yandex.ru/export/html.xml?private_token=1c7f766fab8185a98f934a458b51e7fe8ff5b636&tz_id=Europe/Moscow&limit=90"

# Время отправки ежедневного дайджеста (в часах, по умолчанию 12:00 дня)
SEND_HOUR = 12

# Часовой пояс
TIMEZONE = "Europe/Moscow"