#!/bin/bash
# Скрипт для запуска веб-приложения

# Установите переменные окружения
export GRAPHQL_ENDPOINT="${GRAPHQL_ENDPOINT:-https://your-api-endpoint.com/graphql}"
export FLASK_SECRET_KEY="${FLASK_SECRET_KEY:-change-this-in-production}"

# Запустите приложение
python web_app.py

