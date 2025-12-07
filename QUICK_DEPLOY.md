# ⚡ Быстрый деплой бота

## 🚀 Самый простой способ: Railway.app

### Шаг 1: Подготовка

1. **Создайте GitHub репозиторий:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/ваш_username/literary-calendar-bot.git
   git push -u origin main
   ```

### Шаг 2: Деплой на Railway

1. **Зайдите на [railway.app](https://railway.app)**
2. **Войдите через GitHub**
3. **New Project → Deploy from GitHub repo**
4. **Выберите ваш репозиторий**

### Шаг 3: Настройка переменных

В Railway: **Settings → Variables** → Add:

```
BOT_TOKEN=ваш_токен_бота
GRAPHQL_ENDPOINT=https://ваш-api.com/graphql
GROUP_CHAT_ID=id_вашей_группы
CALENDAR_URL=https://calendar.yandex.ru/export/html.xml?...
```

### Шаг 4: Запуск

Railway автоматически задеплоит бота! ✅

---

## 🐳 Альтернатива: Docker

Если у вас есть сервер:

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/ваш_username/literary-calendar-bot.git
cd literary-calendar-bot

# 2. Создайте .env файл
cat > .env << EOF
BOT_TOKEN=ваш_токен
GRAPHQL_ENDPOINT=https://ваш-api.com/graphql
GROUP_CHAT_ID=id_группы
CALENDAR_URL=https://calendar.yandex.ru/export/html.xml?...
EOF

# 3. Запустите через Docker
docker-compose up -d

# 4. Проверьте логи
docker-compose logs -f
```

---

## 📋 Чеклист перед деплоем

- [ ] Все файлы закоммичены в Git
- [ ] `requirements_bot.txt` содержит все зависимости
- [ ] Переменные окружения настроены
- [ ] Бот протестирован локально (`python test_bot.py`)

---

**Готово! Бот работает 24/7** 🎉

