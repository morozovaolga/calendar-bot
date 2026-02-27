@echo off
REM Скрипт для установки библиотек на Windows
chcp 65001 >nul
echo ============================================================
echo 🚀 Установка библиотек для проекта calendar-bot
echo ============================================================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.8 или выше.
    pause
    exit /b 1
)

echo ✅ Python найден
python --version
echo.

REM Обновляем pip
echo 🔄 Обновление pip...
python -m pip install --upgrade pip
echo.

REM Устанавливаем пакеты из requirements.txt
if exist requirements.txt (
    echo 📦 Установка пакетов из requirements.txt...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ⚠️  Произошли ошибки при установке
        echo 💡 Попробуйте установить вручную:
        echo    pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo.
    echo ✅ Все пакеты успешно установлены!
) else (
    echo ⚠️  Файл requirements.txt не найден!
    echo 📦 Устанавливаю основные библиотеки...
    python -m pip install pandas openpyxl requests beautifulsoup4 Flask python-telegram-bot
)

echo.
echo ============================================================
echo ✅ Установка завершена!
echo ============================================================
echo.
pause

