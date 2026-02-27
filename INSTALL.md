# Установка библиотек

Для установки всех необходимых библиотек проекта используйте один из способов:

## Способ 1: Python скрипт (рекомендуется)

```bash
python install_requirements.py
```

## Способ 2: Windows Batch файл

Просто запустите двойным кликом:
```
install_requirements.bat
```

Или из командной строки:
```cmd
install_requirements.bat
```

## Способ 3: Linux/Mac Shell скрипт

```bash
chmod +x install_requirements.sh
./install_requirements.sh
```

## Способ 4: Прямая установка через pip

```bash
pip install -r requirements.txt
```

Или для Python 3:
```bash
pip3 install -r requirements.txt
```

## Основные библиотеки проекта

- **pandas** - работа с данными и Excel файлами
- **openpyxl** - чтение/запись Excel файлов
- **requests** - HTTP запросы
- **beautifulsoup4** - парсинг HTML
- **Flask** - веб-интерфейс
- **python-telegram-bot** - Telegram бот

## Проверка установки

После установки проверьте установленные пакеты:

```bash
pip list
```

Или проверьте конкретный пакет:

```bash
python -c "import pandas; print('pandas установлен')"
```

