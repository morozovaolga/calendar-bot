# Telegram-бот литературного календаря

Бот для ежедневной рассылки литературных дат из календаря Yandex Calendar с ссылками на книги из API "Свет".

## 🎯 Функционал

- 📅 Парсит календарь литературных дат из Yandex Calendar
- 📚 Автоматически находит книги авторов через GraphQL API
- 🔗 Формирует красивые сообщения со ссылками на книги
- ⏰ Отправляет ежедневную рассылку в группу Telegram
- 🎨 Форматирует сообщения с эмодзи и ссылками

## 📋 Требования

- Python 3.8+
- Telegram бот (получить токен у @BotFather)
- Доступ к GraphQL API "Свет"
- Группа в Telegram для рассылки

## 🚀 Установка

1. **Установите зависимости:**

```bash
pip install -r requirements_bot.txt
```

2. **Настройте конфигурацию:**

Откройте `literary_calendar_bot_config.py` и заполните:

```python
BOT_TOKEN = "ваш_токен_бота"
GRAPHQL_ENDPOINT = "https://ваш-api-endpoint.com/graphql"
GROUP_CHAT_ID = "id_вашей_группы"
```

3. **Получите токен бота:**

- Откройте [@BotFather](https://t.me/BotFather) в Telegram
- Отправьте `/newbot`
- Следуйте инструкциям
- Скопируйте токен в конфиг

4. **Получите ID группы:**

- Добавьте бота [@userinfobot](https://t.me/userinfobot) в вашу группу
- Он покажет ID группы
- Или используйте [@RawDataBot](https://t.me/RawDataBot)

## 💻 Использование

### Вариант 1: Запуск с конфигурационным файлом

```python
from literary_calendar_bot import LiteraryCalendarBot
import asyncio
import literary_calendar_bot_config as config

async def main():
    bot = LiteraryCalendarBot(
        bot_token=config.BOT_TOKEN,
        calendar_url=config.CALENDAR_URL,
        graphql_endpoint=config.GRAPHQL_ENDPOINT,
        group_chat_id=config.GROUP_CHAT_ID
    )
    await bot.run_daily()

if __name__ == "__main__":
    asyncio.run(main())
```

### Вариант 2: Ручная отправка (для тестирования)

```python
from literary_calendar_bot import LiteraryCalendarBot
import asyncio
import literary_calendar_bot_config as config

async def test():
    bot = LiteraryCalendarBot(
        bot_token=config.BOT_TOKEN,
        calendar_url=config.CALENDAR_URL,
        graphql_endpoint=config.GRAPHQL_ENDPOINT,
        group_chat_id=config.GROUP_CHAT_ID
    )
    # Отправляем события на сегодня
    await bot.send_daily_digest()

asyncio.run(test())
```

### Вариант 3: Запуск как сервис (Linux)

Создайте файл `/etc/systemd/system/literary-bot.service`:

```ini
[Unit]
Description=Literary Calendar Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 /path/to/bot/literary_calendar_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Запуск:

```bash
sudo systemctl enable literary-bot
sudo systemctl start literary-bot
```

## 📝 Пример сообщения

Бот отправляет сообщения в таком формате:

```
📚 Антон Чехов родился в 1860 году

📅 29 января 2026

Книги Чехова в приложении

📖 Книги в приложении «Свет»:
• Вишневый сад
• Дама с собачкой
• Палата №6

🔗 Ссылки:
Открыть в каталоге
```

## 🔧 Настройка

### Изменение времени отправки

В `literary_calendar_bot_config.py`:

```python
SEND_HOUR = 9  # Измените на нужное время (0-23)
```

В коде бота измените проверку времени:

```python
if now.hour == SEND_HOUR and now.minute == 0:
```

### Ограничение количества книг

В методе `format_event_message` измените:

```python
for book in books[:5]:  # Измените 5 на нужное число
```

### Фильтрация событий

Добавьте фильтры в метод `get_today_events`:

```python
# Например, только события с авторами
today_events = [e for e in today_events if e['author_uuids']]
```

## 🐛 Решение проблем

### Бот не отправляет сообщения

1. Проверьте токен бота
2. Убедитесь, что бот добавлен в группу
3. Проверьте ID группы
4. Посмотрите логи бота

### Ошибки парсинга календаря

Календарь Yandex может менять формат. Если парсинг не работает:

1. Проверьте формат XML/HTML календаря
2. Обновите метод `parse_calendar` под новый формат
3. Используйте альтернативный метод `_simple_parse`

### Ошибки API

1. Проверьте URL GraphQL API
2. Убедитесь, что API доступен
3. Проверьте формат запросов в логах

## 📚 Дополнительные возможности

### Добавление команд боту

```python
from telegram import Update
from telegram.ext import Application, CommandHandler

async def start(update: Update, context):
    await update.message.reply_text("Привет! Я бот литературного календаря.")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.run_polling()
```

### Отправка по запросу

Добавьте команду `/today`:

```python
async def today_command(update: Update, context):
    bot = LiteraryCalendarBot(...)
    await bot.send_daily_digest()
```

### Уведомления о предстоящих событиях

Модифицируйте `get_today_events` для получения событий на несколько дней вперед.

## 📄 Лицензия

Свободное использование для некоммерческих целей.

## 🤝 Вклад

Если нашли ошибки или хотите улучшить бота - создайте issue или pull request!
