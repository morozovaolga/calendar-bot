# 🚀 Деплой бота на Vercel

## ⚠️ Важно: Ограничения Vercel

Vercel **НЕ подходит** для долгоживущих процессов (как наш бот с `run_daily()`).

**Почему:**
- ❌ Vercel работает на serverless функциях
- ❌ Максимальное время выполнения: 60 секунд (на бесплатном плане)
- ❌ Не поддерживает постоянно работающие процессы
- ❌ Функции запускаются только по запросу

## ✅ Решение: Vercel Cron Jobs + Serverless функция

Можно использовать Vercel **Cron Jobs** для запуска функции по расписанию!

---

## 📋 Вариант 1: Vercel Cron Jobs (Рекомендуется)

### Как это работает:

1. **Serverless функция** запускается по расписанию (через Cron)
2. Выполняет отправку сообщений
3. Завершается (не работает постоянно)

### Шаг 1: Создайте структуру проекта

```
vercel-bot/
├── api/
│   └── send-daily.js  (или send-daily.py)
├── vercel.json
└── requirements.txt
```

### Шаг 2: Создайте serverless функцию

**`api/send-daily.py`** (Python через Vercel Python Runtime):

```python
from http.server import BaseHTTPRequestHandler
import json
import asyncio
import os
from literary_calendar_bot import LiteraryCalendarBot

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Получаем переменные окружения
        bot_token = os.environ.get('BOT_TOKEN')
        graphql_endpoint = os.environ.get('GRAPHQL_ENDPOINT')
        group_chat_id = os.environ.get('GROUP_CHAT_ID')
        calendar_url = os.environ.get('CALENDAR_URL')
        
        # Создаем бота
        bot = LiteraryCalendarBot(
            bot_token=bot_token,
            calendar_url=calendar_url,
            graphql_endpoint=graphql_endpoint,
            group_chat_id=group_chat_id
        )
        
        # Запускаем отправку
        try:
            asyncio.run(bot.send_daily_digest())
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'success',
                'message': 'Daily digest sent'
            }).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'error',
                'message': str(e)
            }).encode())
```

**Или используйте Node.js** (более надежно на Vercel):

**`api/send-daily.js`**:

```javascript
const { spawn } = require('child_process');

export default async function handler(req, res) {
  // Проверяем секретный ключ (для безопасности)
  if (req.headers.authorization !== `Bearer ${process.env.CRON_SECRET}`) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  // Запускаем Python скрипт
  const python = spawn('python3', ['send_daily.py']);
  
  let output = '';
  python.stdout.on('data', (data) => {
    output += data.toString();
  });

  python.on('close', (code) => {
    if (code === 0) {
      res.status(200).json({ 
        status: 'success',
        output: output 
      });
    } else {
      res.status(500).json({ 
        status: 'error',
        output: output 
      });
    }
  });
}
```

### Шаг 3: Настройте Cron в `vercel.json`

```json
{
  "crons": [
    {
      "path": "/api/send-daily",
      "schedule": "0 9 * * *"
    }
  ],
  "functions": {
    "api/send-daily.js": {
      "maxDuration": 60
    }
  }
}
```

**Расписание Cron:**
- `0 9 * * *` - каждый день в 9:00 UTC
- `0 12 * * *` - каждый день в 12:00 UTC (для Москвы +3 часа = 15:00)

### Шаг 4: Создайте упрощенный скрипт

**`send_daily.py`** (в корне проекта):

```python
import asyncio
import os
import sys
from literary_calendar_bot import LiteraryCalendarBot

async def main():
    bot = LiteraryCalendarBot(
        bot_token=os.environ['BOT_TOKEN'],
        calendar_url=os.environ['CALENDAR_URL'],
        graphql_endpoint=os.environ['GRAPHQL_ENDPOINT'],
        group_chat_id=os.environ['GROUP_CHAT_ID']
    )
    
    await bot.send_daily_digest()
    print("✅ Daily digest sent successfully")

if __name__ == "__main__":
    asyncio.run(main())
```

### Шаг 5: Деплой на Vercel

```bash
# Установите Vercel CLI
npm i -g vercel

# Войдите
vercel login

# Деплой
vercel

# Добавьте переменные окружения
vercel env add BOT_TOKEN
vercel env add GRAPHQL_ENDPOINT
vercel env add GROUP_CHAT_ID
vercel env add CALENDAR_URL
vercel env add CRON_SECRET  # Секретный ключ для безопасности
```

---

## 📋 Вариант 2: Vercel + External Cron (Проще)

Используйте внешний сервис для запуска функции по расписанию:

### Варианты внешних cron сервисов:

1. **cron-job.org** (бесплатно)
2. **EasyCron** (бесплатный план)
3. **UptimeRobot** (бесплатно)

### Настройка:

1. **Создайте API endpoint на Vercel:**

**`api/send-daily.js`**:

```javascript
export default async function handler(req, res) {
  // Проверяем секретный ключ
  const secret = req.query.secret || req.headers['x-cron-secret'];
  if (secret !== process.env.CRON_SECRET) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  // Здесь можно вызвать Python через API или использовать Node.js библиотеки
  // Для простоты используем HTTP запрос к другому endpoint
  
  try {
    // Выполняем отправку
    const response = await fetch(process.env.INTERNAL_API_URL + '/send', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.INTERNAL_SECRET}`
      }
    });
    
    res.status(200).json({ status: 'success' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}
```

2. **Настройте cron-job.org:**
   - URL: `https://ваш-проект.vercel.app/api/send-daily?secret=ваш_секрет`
   - Расписание: Ежедневно в 9:00
   - Метод: GET или POST

---

## ⚡ Вариант 3: Vercel + GitHub Actions (Лучший вариант!)

Используйте GitHub Actions для запуска по расписанию:

### `.github/workflows/daily-bot.yml`:

```yaml
name: Daily Bot Send

on:
  schedule:
    - cron: '0 9 * * *'  # Каждый день в 9:00 UTC
  workflow_dispatch:  # Ручной запуск

jobs:
  send:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements_bot.txt
      
      - name: Send daily digest
        env:
          BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
          GRAPHQL_ENDPOINT: ${{ secrets.GRAPHQL_ENDPOINT }}
          GROUP_CHAT_ID: ${{ secrets.GROUP_CHAT_ID }}
          CALENDAR_URL: ${{ secrets.CALENDAR_URL }}
        run: |
          python send_daily.py
```

**Преимущества:**
- ✅ Бесплатно
- ✅ Надежно
- ✅ Не зависит от Vercel
- ✅ Можно запускать вручную

---

## 💰 Стоимость и лимиты Vercel

### Бесплатный план:
- ✅ 100 GB-hours функций в месяц
- ✅ Cron jobs включены
- ⚠️ Максимальное время выполнения: 60 секунд
- ⚠️ Функции "засыпают" после неактивности

### Pro план ($20/месяц):
- ✅ 1000 GB-hours функций
- ✅ Максимальное время выполнения: 300 секунд
- ✅ Больше ресурсов

---

## 🎯 Рекомендация

**Для этого бота лучше использовать:**

1. **Railway.app** ⭐ (лучший вариант)
   - Поддерживает долгоживущие процессы
   - Бесплатный план достаточен
   - Простая настройка

2. **GitHub Actions + Vercel** (если хотите Vercel)
   - GitHub Actions запускает функцию по расписанию
   - Vercel хранит код
   - Бесплатно

3. **Render.com** (альтернатива Railway)
   - Аналогично Railway
   - Бесплатный план

**Vercel сам по себе НЕ подходит** для постоянно работающего бота, но можно использовать в комбинации с GitHub Actions или внешними cron сервисами.

---

## 📊 Сравнение вариантов

| Вариант | Стоимость | Надежность | Простота | Подходит? |
|---------|-----------|------------|----------|-----------|
| Vercel Cron | Бесплатно | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⚠️ Ограничения |
| Vercel + GitHub Actions | Бесплатно | ⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ Да |
| Railway | Бесплатно | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅✅ Лучший |
| Render | Бесплатно | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ✅ Да |
| VPS | $5-10/мес | ⭐⭐⭐⭐⭐ | ⭐⭐ | ✅✅ Продакшен |

---

## 🚀 Быстрый старт с Vercel + GitHub Actions

1. **Создайте `.github/workflows/daily-bot.yml`** (код выше)

2. **Добавьте секреты в GitHub:**
   - Settings → Secrets → Actions → New secret
   - Добавьте: `BOT_TOKEN`, `GRAPHQL_ENDPOINT`, `GROUP_CHAT_ID`, `CALENDAR_URL`

3. **Закоммитьте и запушьте:**
   ```bash
   git add .github/workflows/daily-bot.yml
   git commit -m "Add daily bot workflow"
   git push
   ```

4. **Готово!** GitHub Actions будет запускать бота каждый день в 9:00 UTC

---

**Вывод:** Vercel сам по себе не выдержит постоянно работающий бот, но в комбинации с GitHub Actions или внешними cron сервисами - да! 🎉

