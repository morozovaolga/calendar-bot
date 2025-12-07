"""
Скрипт для вывода ближайших событий из базы данных
Показывает первые 10 событий за следующие 10 дней
"""

from datetime import datetime, timedelta
from database import EventDatabase

def show_upcoming_events():
    """Выводит события на следующие 10 дней"""
    
    print("=" * 60)
    print("📅 БЛИЖАЙШИЕ СОБЫТИЯ (СЛЕДУЮЩИЕ 10 ДНЕЙ)")
    print("=" * 60)
    
    # Инициализируем базу данных
    db = EventDatabase()
    
    # Получаем сегодняшнюю дату
    today = datetime.now().date()
    end_date = today + timedelta(days=10)
    
    print(f"\n📆 Период: {today.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}")
    print(f"📅 Сегодня: {today.strftime('%d %B %Y')}")
    print("-" * 60)
    
    # Получаем все события
    all_events = db.get_all_events(is_active=True)
    
    # Фильтруем события на следующие 10 дней
    upcoming_events = []
    for event in all_events:
        event_date = event['event_date']
        if today <= event_date <= end_date:
            upcoming_events.append(event)
    
    # Сортируем по дате
    upcoming_events.sort(key=lambda x: x['event_date'])
    
    print(f"\n✅ Найдено событий: {len(upcoming_events)}")
    
    if not upcoming_events:
        print("\n⚠️ Событий на следующие 10 дней не найдено")
        print("\n💡 Попробуйте:")
        print("   1. Импортировать события: python quick_import.py")
        print("   2. Добавить события через веб-форму: python web_app.py")
        return
    
    # Выводим первые 10 событий
    print(f"\n📋 Первые 10 событий:\n")
    
    for i, event in enumerate(upcoming_events[:10], 1):
        event_date = event['event_date']
        days_until = (event_date - today).days
        
        # Определяем статус
        if days_until == 0:
            status = "🎯 СЕГОДНЯ"
        elif days_until == 1:
            status = "📅 ЗАВТРА"
        else:
            status = f"📅 Через {days_until} дней"
        
        print(f"{i}. {status}")
        print(f"   📚 {event['title']}")
        print(f"   📆 Дата: {event_date.strftime('%d %B %Y')} ({event_date.strftime('%d.%m.%Y')})")
        
        if event.get('description'):
            desc = event['description'][:100]
            if len(event.get('description', '')) > 100:
                desc += "..."
            print(f"   📝 {desc}")
        
        if event.get('reference_name'):
            ref_type = {
                'author': '👤 Автор',
                'tag': '🏷️ Тег',
                'category': '📂 Категория'
            }.get(event['event_type'], '🔗 Ссылка')
            print(f"   {ref_type}: {event['reference_name']}")
        
        print()
    
    # Показываем статистику
    print("-" * 60)
    print(f"📊 Статистика:")
    print(f"   Всего событий в базе: {len(all_events)}")
    print(f"   Событий на следующие 10 дней: {len(upcoming_events)}")
    print(f"   Показано: {min(10, len(upcoming_events))}")
    
    if len(upcoming_events) > 10:
        print(f"\n💡 Еще {len(upcoming_events) - 10} событий не показано")
    
    print("=" * 60)

if __name__ == "__main__":
    show_upcoming_events()

