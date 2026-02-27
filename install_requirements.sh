#!/bin/bash
# Скрипт для установки библиотек на Linux/Mac

echo "============================================================"
echo "🚀 Установка библиотек для проекта calendar-bot"
echo "============================================================"
echo ""

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден! Установите Python 3.8 или выше."
    exit 1
fi

echo "✅ Python найден"
python3 --version
echo ""

# Обновляем pip
echo "🔄 Обновление pip..."
python3 -m pip install --upgrade pip
echo ""

# Устанавливаем пакеты из requirements.txt
if [ -f "requirements.txt" ]; then
    echo "📦 Установка пакетов из requirements.txt..."
    python3 -m pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        echo ""
        echo "⚠️  Произошли ошибки при установке"
        echo "💡 Попробуйте установить вручную:"
        echo "   pip3 install -r requirements.txt"
        exit 1
    fi
    
    echo ""
    echo "✅ Все пакеты успешно установлены!"
else
    echo "⚠️  Файл requirements.txt не найден!"
    echo "📦 Устанавливаю основные библиотеки..."
    python3 -m pip install pandas openpyxl requests beautifulsoup4 Flask python-telegram-bot
fi

echo ""
echo "============================================================"
echo "✅ Установка завершена!"
echo "============================================================"
echo ""

