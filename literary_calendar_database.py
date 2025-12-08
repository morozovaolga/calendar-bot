"""
Структура базы данных для литературного календаря
Поддерживает ежегодные события с привязкой к книгам, авторам, тегам и категориям
"""

import sqlite3
import csv
from datetime import datetime
from typing import List, Dict, Optional
import json


class LiteraryCalendarDatabase:
    """База данных литературного календаря"""
    
    def __init__(self, db_path: str = None):
        # Используем путь из конфига, если не указан явно
        if db_path is None:
            try:
                from literary_calendar_bot_config import DB_PATH
                db_path = DB_PATH
            except (ImportError, AttributeError):
                db_path = "literary_events.db"
        
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # Таблица событий
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_date TEXT NOT NULL,  -- Формат: MM-DD (месяц-день для ежегодных событий)
                event_type TEXT NOT NULL,  -- 'birthday', 'death', 'book_published', 'memorable_day'
                title TEXT NOT NULL,       -- Заголовок события
                description TEXT,          -- Описание события
                author_name TEXT,          -- Имя автора (если применимо)
                book_title TEXT,           -- Название книги (если применимо)
                year INTEGER,              -- Год события (NULL если ежегодное)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Таблица ссылок на API ресурсы (многие-ко-многим)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_references (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                reference_type TEXT NOT NULL,  -- 'author', 'book', 'tag', 'category', 'film', 'article'
                reference_uuid TEXT,           -- UUID в вашем API (для author, book, category)
                reference_slug TEXT,           -- Slug в вашем API (для book)
                reference_name TEXT,           -- Название для отображения
                priority INTEGER DEFAULT 0,    -- Приоритет отображения (0 - высший)
                metadata TEXT,                 -- JSON с дополнительными данными (обложка, аннотация и т.д.)
                FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
            )
        """)
        
        # Индексы для быстрого поиска
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_date ON events(event_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON events(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reference_type ON event_references(reference_type)")
        
        self.conn.commit()
    
    def add_event(
        self, 
        month: int, 
        day: int, 
        event_type: str, 
        title: str,
        description: str = None,
        author_name: str = None,
        book_title: str = None,
        year: int = None
    ) -> int:
        """
        Добавляет событие в базу
        
        Args:
            month: Месяц (1-12)
            day: День (1-31)
            event_type: Тип события ('birthday', 'death', 'book_published', 'memorable_day')
            title: Заголовок
            description: Описание
            author_name: Имя автора
            book_title: Название книги
            year: Год события (опционально)
        
        Returns:
            ID созданного события
        """
        event_date = f"{month:02d}-{day:02d}"
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO events (event_date, event_type, title, description, author_name, book_title, year)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (event_date, event_type, title, description, author_name, book_title, year))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def add_reference(
        self,
        event_id: int,
        reference_type: str,
        reference_uuid: str = None,
        reference_slug: str = None,
        reference_name: str = None,
        priority: int = 0,
        metadata: Dict = None
    ):
        """
        Добавляет ссылку на API ресурс к событию
        
        Args:
            event_id: ID события
            reference_type: Тип ('author', 'book', 'tag', 'category', 'film', 'article')
            reference_uuid: UUID в API
            reference_slug: Slug в API
            reference_name: Название для отображения
            priority: Приоритет (0 = высший)
            metadata: Дополнительные данные (обложка, аннотация и т.д.)
        """
        cursor = self.conn.cursor()
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute("""
            INSERT INTO event_references 
            (event_id, reference_type, reference_uuid, reference_slug, reference_name, priority, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (event_id, reference_type, reference_uuid, reference_slug, reference_name, priority, metadata_json))
        
        self.conn.commit()
    
    def get_events_by_date(self, month: int, day: int) -> List[Dict]:
        """Получает все события на заданную дату"""
        event_date = f"{month:02d}-{day:02d}"
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM events WHERE event_date = ?
            ORDER BY event_type, year DESC
        """, (event_date,))
        
        events = []
        for row in cursor.fetchall():
            event = dict(row)
            # Получаем все ссылки для этого события
            event['references'] = self.get_event_references(event['id'])
            events.append(event)
        
        return events
    
    def get_event_references(self, event_id: int) -> List[Dict]:
        """Получает все ссылки для события"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM event_references 
            WHERE event_id = ?
            ORDER BY priority, id
        """, (event_id,))
        
        references = []
        for row in cursor.fetchall():
            ref = dict(row)
            if ref['metadata']:
                ref['metadata'] = json.loads(ref['metadata'])
            references.append(ref)
        
        return references
    
    def import_from_csv(self, csv_path: str):
        """
        Импортирует события из CSV файла
        
        Формат CSV:
        month,day,event_type,title,description,author_name,book_title,year,
        reference_type,reference_uuid,reference_slug,reference_name,priority,metadata_json
        """
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Добавляем событие
                event_id = self.add_event(
                    month=int(row['month']),
                    day=int(row['day']),
                    event_type=row['event_type'],
                    title=row['title'],
                    description=row.get('description') or None,
                    author_name=row.get('author_name') or None,
                    book_title=row.get('book_title') or None,
                    year=int(row['year']) if row.get('year') else None
                )
                
                # Добавляем ссылки (если есть)
                if row.get('reference_type'):
                    metadata = None
                    if row.get('metadata_json'):
                        try:
                            metadata = json.loads(row['metadata_json'])
                        except:
                            pass
                    
                    self.add_reference(
                        event_id=event_id,
                        reference_type=row['reference_type'],
                        reference_uuid=row.get('reference_uuid') or None,
                        reference_slug=row.get('reference_slug') or None,
                        reference_name=row.get('reference_name') or None,
                        priority=int(row.get('priority', 0)),
                        metadata=metadata
                    )
    
    def export_to_csv(self, csv_path: str):
        """Экспортирует события в CSV файл"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                e.*,
                r.reference_type,
                r.reference_uuid,
                r.reference_slug,
                r.reference_name,
                r.priority,
                r.metadata
            FROM events e
            LEFT JOIN event_references r ON e.id = r.event_id
            ORDER BY e.event_date, e.id, r.priority
        """)
        
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            fieldnames = [
                'month', 'day', 'event_type', 'title', 'description', 
                'author_name', 'book_title', 'year',
                'reference_type', 'reference_uuid', 'reference_slug', 
                'reference_name', 'priority', 'metadata_json'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in cursor.fetchall():
                month, day = row['event_date'].split('-')
                writer.writerow({
                    'month': month,
                    'day': day,
                    'event_type': row['event_type'],
                    'title': row['title'],
                    'description': row['description'] or '',
                    'author_name': row['author_name'] or '',
                    'book_title': row['book_title'] or '',
                    'year': row['year'] or '',
                    'reference_type': row['reference_type'] or '',
                    'reference_uuid': row['reference_uuid'] or '',
                    'reference_slug': row['reference_slug'] or '',
                    'reference_name': row['reference_name'] or '',
                    'priority': row['priority'] if row['priority'] is not None else '',
                    'metadata_json': row['metadata'] or ''
                })
    
    def close(self):
        """Закрывает соединение с БД"""
        if self.conn:
            self.conn.close()


# Пример использования
if __name__ == "__main__":
    db = LiteraryCalendarDatabase()
    
    # Пример 1: День рождения Пушкина с книгами
    event_id = db.add_event(
        month=6,
        day=6,
        event_type='birthday',
        title='День рождения Александра Сергеевича Пушкина',
        description='Родился величайший русский поэт',
        author_name='Александр Пушкин',
        year=1799
    )
    
    # Добавляем ссылку на автора в API
    db.add_reference(
        event_id=event_id,
        reference_type='author',
        reference_uuid='550e8400-e29b-41d4-a716-446655440000',  # UUID автора в вашем API
        reference_name='Александр Пушкин',
        priority=0
    )
    
    # Добавляем конкретную книгу
    db.add_reference(
        event_id=event_id,
        reference_type='book',
        reference_uuid='660e8400-e29b-41d4-a716-446655440001',
        reference_slug='evgenij-onegin',
        reference_name='Евгений Онегин',
        priority=1,
        metadata={
            'cover_url': 'https://example.com/images/covers/onegin.jpg',
            'annotation': 'Роман в стихах'
        }
    )
    
    # Пример 2: Памятный день литературы с тегом
    event_id = db.add_event(
        month=3,
        day=21,
        event_type='memorable_day',
        title='Всемирный день поэзии',
        description='Отмечается по решению ЮНЕСКО'
    )
    
    db.add_reference(
        event_id=event_id,
        reference_type='tag',
        reference_uuid='770e8400-e29b-41d4-a716-446655440002',
        reference_name='Поэзия',
        priority=0
    )
    
    # Экспорт в CSV
    db.export_to_csv('literary_calendar.csv')
    
    print("✅ База данных создана и экспортирована в CSV")
    print("📅 Пример событий добавлен")
    
    # Проверка: получаем события на 6 июня
    events = db.get_events_by_date(6, 6)
    print(f"\n📚 События на 6 июня: {len(events)}")
    for event in events:
        print(f"  - {event['title']}")
        for ref in event['references']:
            print(f"    → {ref['reference_type']}: {ref['reference_name']}")
    
    db.close()