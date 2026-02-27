#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Веб-интерфейс для управления литературным календарём
Flask приложение для добавления, редактирования и удаления событий
"""

import os

from dotenv import load_dotenv

from web.app import create_app

load_dotenv()
app = create_app(os.getenv("DB_PATH", "literary_events.db"))

if __name__ == '__main__':
    print("🚀 Запуск веб-интерфейса редактора календаря...")
    print("📍 Откройте: http://localhost:5000")
    print("✅ Для остановки нажмите Ctrl+C\n")
    app.run(debug=True, host='localhost', port=5000)
