#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для установки всех необходимых библиотек проекта
"""

import subprocess
import sys
import os

def check_python_version():
    """Проверяет версию Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("[ERROR] Требуется Python 3.8 или выше!")
        print(f"   Текущая версия: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
    return True

def install_package(package):
    """Устанавливает пакет через pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        return False

def install_from_requirements():
    """Устанавливает пакеты из requirements.txt"""
    requirements_file = "requirements.txt"
    
    if not os.path.exists(requirements_file):
        print(f"[WARNING] Файл {requirements_file} не найден!")
        print("   Устанавливаю основные библиотеки вручную...")
        
        # Основные библиотеки для проекта
        essential_packages = [
            "pandas",
            "openpyxl",
            "requests",
            "beautifulsoup4",
            "Flask",
            "python-telegram-bot"
        ]
        
        print(f"\n[INFO] Установка основных библиотек ({len(essential_packages)} пакетов)...")
        for package in essential_packages:
            print(f"   Установка {package}...", end=" ", flush=True)
            if install_package(package):
                print("[OK]")
            else:
                print("[FAIL]")
        
        return
    
    print(f"[INFO] Установка пакетов из {requirements_file}...")
    
    try:
        # Пробуем разные кодировки для чтения файла
        encodings = ['utf-8', 'utf-8-sig', 'cp1251', 'latin-1']
        packages = []
        
        for encoding in encodings:
            try:
                with open(requirements_file, 'r', encoding=encoding) as f:
                    packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                break
            except UnicodeDecodeError:
                continue
        
        if packages:
            total = len(packages)
            print(f"   Найдено {total} пакетов для установки\n")
        
        # Устанавливаем через pip install -r requirements.txt
        print("[INFO] Запуск pip install...")
        print("   (Это может занять некоторое время...)\n")
        
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", requirements_file]
        )
        
        if result.returncode == 0:
            print("\n[OK] Все пакеты успешно установлены!")
        else:
            print("\n[WARNING] Произошли ошибки при установке")
            print("[INFO] Попробуйте установить вручную:")
            print(f"   pip install -r {requirements_file}")
            
    except Exception as e:
        print(f"[ERROR] Ошибка: {e}")
        print("\n[INFO] Попробуйте установить вручную:")
        print(f"   pip install -r {requirements_file}")

def upgrade_pip():
    """Обновляет pip до последней версии"""
    print("[INFO] Обновление pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
        print("[OK] pip обновлен")
        return True
    except:
        print("[WARNING] Не удалось обновить pip (продолжаем...)")
        return False

def check_venv():
    """Проверяет, работает ли скрипт в виртуальном окружении"""
    in_venv = (hasattr(sys, 'real_prefix') or 
               (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
    
    if in_venv:
        print(f"[INFO] Работаем в виртуальном окружении: {sys.prefix}")
    else:
        print("[WARNING] Виртуальное окружение не активировано")
        print("[INFO] Рекомендуется использовать виртуальное окружение:")
        print("   python -m venv .venv")
        print("   .venv\\Scripts\\activate  (Windows)")
        print("   source .venv/bin/activate  (Linux/Mac)")
    print()
    return in_venv

def main():
    print("=" * 60)
    print("Установка библиотек для проекта calendar-bot")
    print("=" * 60)
    print()
    
    # Проверяем версию Python
    if not check_python_version():
        sys.exit(1)
    
    print()
    
    # Проверяем виртуальное окружение
    check_venv()
    
    # Обновляем pip
    upgrade_pip()
    print()
    
    # Устанавливаем пакеты
    install_from_requirements()
    
    print()
    print("=" * 60)
    print("[OK] Установка завершена!")
    print("=" * 60)
    print()
    print("[INFO] Для проверки установленных пакетов используйте:")
    print("   pip list")
    print()

if __name__ == '__main__':
    main()

