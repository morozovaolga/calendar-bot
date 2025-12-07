"""
Модуль для работы с базой данных событий
Использует SQLite для простоты
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path("literary_events.db")


class EventDatabase:
    """Класс для работы с базой данных событий"""
    
    def __init__(self, db_path: str = None):
        """
        Инициализация базы данных
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path or str(DB_PATH)
        self.init_database()
    
    def get_connection(self):
        """Получает соединение с базой данных"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Возвращает результаты как словари
        return conn
    
    def init_database(self):
        """Создает таблицы в базе данных"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица событий
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                event_date DATE NOT NULL,
                event_type TEXT NOT NULL,  -- 'author', 'tag', 'category', 'custom'
                reference_uuid TEXT,  -- UUID автора, тега или категории
                reference_name TEXT,  -- Название для отображения
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Индекс для быстрого поиска по дате
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_event_date 
            ON events(event_date)
        """)
        
        # Индекс для поиска активных событий
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_is_active 
            ON events(is_active)
        """)
        
        conn.commit()
        conn.close()
        logger.info("База данных инициализирована")
    
    def add_event(
        self,
        title: str,
        event_date: datetime,
        event_type: str,
        description: str = None,
        reference_uuid: str = None,
        reference_name: str = None,
        is_active: bool = True
    ) -> int:
        """
        Добавляет новое событие
        
        Returns:
            ID созданного события
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO events 
            (title, description, event_date, event_type, reference_uuid, reference_name, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            description,
            event_date.date(),
            event_type,
            reference_uuid,
            reference_name,
            is_active
        ))
        
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Добавлено событие: {title} ({event_date.date()})")
        return event_id
    
    def get_events_by_date(self, date: datetime) -> List[Dict]:
        """
        Получает события на указанную дату
        
        Args:
            date: Дата для поиска
            
        Returns:
            Список событий
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM events
            WHERE event_date = ? AND is_active = 1
            ORDER BY event_date, title
        """, (date.date(),))
        
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            events.append({
                'id': row['id'],
                'title': row['title'],
                'description': row['description'],
                'event_date': datetime.strptime(row['event_date'], '%Y-%m-%d').date(),
                'event_type': row['event_type'],
                'reference_uuid': row['reference_uuid'],
                'reference_name': row['reference_name'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return events
    
    def get_all_events(
        self,
        limit: int = None,
        offset: int = 0,
        is_active: bool = True
    ) -> List[Dict]:
        """Получает все события"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM events
            WHERE is_active = ?
            ORDER BY event_date DESC, title
        """
        params = [is_active]
        
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        events = []
        for row in rows:
            events.append({
                'id': row['id'],
                'title': row['title'],
                'description': row['description'],
                'event_date': datetime.strptime(row['event_date'], '%Y-%m-%d').date(),
                'event_type': row['event_type'],
                'reference_uuid': row['reference_uuid'],
                'reference_name': row['reference_name'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
        
        return events
    
    def update_event(
        self,
        event_id: int,
        title: str = None,
        description: str = None,
        event_date: datetime = None,
        is_active: bool = None
    ) -> bool:
        """Обновляет событие"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if event_date is not None:
            updates.append("event_date = ?")
            params.append(event_date.date())
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(event_id)
        
        query = f"UPDATE events SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Обновлено событие ID: {event_id}")
        return cursor.rowcount > 0
    
    def delete_event(self, event_id: int) -> bool:
        """Удаляет событие (мягкое удаление - устанавливает is_active = 0)"""
        return self.update_event(event_id, is_active=False)
    
    def get_event_by_id(self, event_id: int) -> Optional[Dict]:
        """Получает событие по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'id': row['id'],
            'title': row['title'],
            'description': row['description'],
            'event_date': datetime.strptime(row['event_date'], '%Y-%m-%d').date(),
            'event_type': row['event_type'],
            'reference_uuid': row['reference_uuid'],
            'reference_name': row['reference_name'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }

