# 🚀 БЫСТРЫЙ СТАРТ - Три команды для работы с БД

## 1️⃣ **Веб-интерфейс** (самый удобный!) 🌐

```powershell
# Запуск
python web_calendar_editor.py

# Откройте: http://localhost:5000
```

✨ **Что можно делать:**
- ✏️ Добавлять события
- 🗑️ Удалять события  
- 🔗 Привязывать книги к событиям
- 🔍 Искать события
- 💾 Все сохраняется автоматически

---

## 2️⃣ **CSV импорт/экспорт** 📊

```powershell
# Экспортировать в Excel/CSV
python -c "from literary_calendar_database import LiteraryCalendarDatabase as DB; db = DB(); db.export_to_csv('events.csv'); print('✅ Готово - открыть events.csv')"

# Импортировать из CSV
python -c "from literary_calendar_database import LiteraryCalendarDatabase as DB; db = DB(); db.import_from_csv('events.csv'); print('✅ Готово')"
```

> Примечание: `events.csv`/экспорты — локальные артефакты. Они добавлены в `.gitignore`, чтобы не засорять репозиторий.

📝 **Формат CSV:**
```
month,day,event_type,title,description,author_name,book_title,year
12,25,день рождения,День рождения Ньютона,Английский физик,Исаак Ньютон,,1643
```

---

## 3️⃣ **SQL базданные** - прямое редактирование 🗄️

### Просмотр всех событий:
```powershell
python -c "
import sqlite3
conn = sqlite3.connect('literary_events.db')
c = conn.cursor()
c.execute('SELECT event_date, title FROM events LIMIT 20')
for row in c.fetchall():
    print(f'{row[0]}: {row[1][:50]}')
conn.close()
"
```

### Добавить событие вручную:
```powershell
python -c "
from literary_calendar_database import LiteraryCalendarDatabase
db = LiteraryCalendarDatabase()
db.add_event(12, 25, 'день рождения', 'День рождения Ньютона', '', '', '', '')
db.close()
print('✅ Событие добавлено')
"
```

### Удалить событие:
```powershell
python -c "
import sqlite3
conn = sqlite3.connect('literary_events.db')
c = conn.cursor()
c.execute('DELETE FROM events WHERE id = 1')  # Укажите нужный ID
conn.commit()
conn.close()
print('✅ Удалено')
"
```

---

## 📊 Статистика

```powershell
python -c "
import sqlite3
conn = sqlite3.connect('literary_events.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM events')
print(f'📅 Событий: {c.fetchone()[0]}')
c.execute('SELECT COUNT(*) FROM event_references')
print(f'🔗 References: {c.fetchone()[0]}')
conn.close()
"
```

---

## 🎯 Для разных задач:

| Задача | Инструмент |
|--------|-----------|
| Быстро добавить 1-2 события | Веб-интерфейс (http://localhost:5000) |
| Добавить 50+ событий из файла | CSV импорт |
| Удалить события | Веб-интерфейс или SQL DELETE |
| Связать события с книгами | Веб-интерфейс - вкладка "Ссылки" |
| Перенести БД на другой компьютер | Скопировать файл `literary_events.db` |
| Резервная копия | Скопировать `literary_events.db` |

---

## 🔗 Привязка к книгам

### Через веб-интерфейс (рекомендуется):
1. Откройте http://localhost:5000
2. Вкладка "🔗 Ссылки на книги"
3. Выберите событие
4. Добавьте ссылку на автора/книгу

### Через Python скрипт:
```python
from literary_calendar_database import LiteraryCalendarDatabase

db = LiteraryCalendarDatabase()

# Добавить ссылку на автора к событию с ID=5
db.add_reference(
    event_id=5,
    reference_type='author',
    reference_uuid='author-chekhov',
    reference_slug='anton-chekhov',
    reference_name='Антон Павлович Чехов',
    priority=1
)

# Добавить ссылку на книгу
db.add_reference(
    event_id=5,
    reference_type='book',
    reference_uuid='book-cherry-orchard',
    reference_slug='vishnevy-sad',
    reference_name='Вишневый сад',
    priority=2
)

db.close()
```

---

## 💡 Pro Tips

1. **Используйте веб-интерфейс** - это в 10 раз быстрее SQL команд
2. **Клавиша F5** - обновить страницу если что-то не загрузилось
3. **Сохраняйте CSV** перед большими изменениями - это резервная копия
4. **Проверяйте отправились ли данные** - после добавления должна появиться строка в таблице

---

**Всё готово! Начните с команды:** `python web_calendar_editor.py` 🚀
