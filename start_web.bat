@echo off
REM Скрипт для запуска веб-приложения на Windows

REM Установите переменные окружения
set GRAPHQL_ENDPOINT=https://your-api-endpoint.com/graphql
set FLASK_SECRET_KEY=change-this-in-production

REM Запустите приложение
python web_app.py

pause

