"""
Веб-приложение для управления литературными событиями
Flask приложение с формой для добавления событий
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime
import logging
from database import EventDatabase
import httpx
import asyncio

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Измените в продакшене!

db = EventDatabase()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URL GraphQL API (можно вынести в конфиг)
GRAPHQL_ENDPOINT = "https://svetapp-test.rusneb.ru/graphql"


async def fetch_from_graphql(query: str, variables: dict = None):
    """Выполняет запрос к GraphQL API"""
    if not GRAPHQL_ENDPOINT:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GRAPHQL_ENDPOINT,
                json={"query": query, "variables": variables or {}},
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Ошибка GraphQL запроса: {e}")
    return None


def run_async(coro):
    """Запускает асинхронную функцию"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.route('/')
def index():
    """Главная страница со списком событий"""
    events = db.get_all_events(limit=50)
    return render_template('index.html', events=events)


@app.route('/add', methods=['GET', 'POST'])
def add_event():
    """Страница добавления события"""
    if request.method == 'POST':
        try:
            # Получаем данные из формы
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            event_date_str = request.form.get('event_date', '')
            event_type = request.form.get('event_type', 'custom')
            reference_uuid = request.form.get('reference_uuid', '').strip() or None
            reference_name = request.form.get('reference_name', '').strip() or None
            
            # Валидация
            if not title:
                flash('Название события обязательно!', 'error')
                return redirect(url_for('add_event'))
            
            if not event_date_str:
                flash('Дата события обязательна!', 'error')
                return redirect(url_for('add_event'))
            
            # Парсим дату
            try:
                event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
            except ValueError:
                flash('Неверный формат даты! Используйте формат ГГГГ-ММ-ДД', 'error')
                return redirect(url_for('add_event'))
            
            # Добавляем событие
            event_id = db.add_event(
                title=title,
                description=description,
                event_date=event_date,
                event_type=event_type,
                reference_uuid=reference_uuid,
                reference_name=reference_name
            )
            
            flash(f'Событие "{title}" успешно добавлено!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении события: {e}")
            flash(f'Ошибка при добавлении события: {str(e)}', 'error')
            return redirect(url_for('add_event'))
    
    # GET запрос - показываем форму
    return render_template('add_event.html')


@app.route('/api/authors')
def api_authors():
    """API для получения списка авторов"""
    query = """
    query GetAuthors {
      authors(body: {
        limit: 100
        page: 1
      }) {
        uuid
        firstName
        lastName
        patronymic
        slug
      }
    }
    """
    
    result = run_async(fetch_from_graphql(query))
    
    if result and 'data' in result and 'authors' in result['data']:
        authors = []
        for author in result['data']['authors']:
            name_parts = []
            if author.get('lastName'):
                name_parts.append(author['lastName'])
            if author.get('firstName'):
                name_parts.append(author['firstName'])
            if author.get('patronymic'):
                name_parts.append(author['patronymic'])
            
            full_name = ' '.join(name_parts) if name_parts else 'Неизвестный автор'
            
            authors.append({
                'uuid': author['uuid'],
                'name': full_name,
                'slug': author.get('slug', '')
            })
        
        return jsonify({'authors': authors})
    
    return jsonify({'authors': []})


@app.route('/api/tags')
def api_tags():
    """API для получения списка тегов"""
    query = """
    query GetTags {
      tags(body: {
        limit: 100
      }) {
        uuid
        name
        slug
      }
    }
    """
    
    result = run_async(fetch_from_graphql(query))
    
    if result and 'data' in result and 'tags' in result['data']:
        return jsonify({'tags': result['data']['tags']})
    
    return jsonify({'tags': []})


@app.route('/api/categories')
def api_categories():
    """API для получения списка категорий"""
    query = """
    query GetCategories {
      categories(body: {
        typeView: ALL
      }) {
        uuid
        name
        slug
      }
    }
    """
    
    result = run_async(fetch_from_graphql(query))
    
    if result and 'data' in result and 'categories' in result['data']:
        return jsonify({'categories': result['data']['categories']})
    
    return jsonify({'categories': []})


@app.route('/api/events/today')
def api_events_today():
    """API для получения событий на сегодня"""
    today = datetime.now()
    events = db.get_events_by_date(today)
    
    # Преобразуем в формат для бота
    formatted_events = []
    for event in events:
        formatted_events.append({
            'title': event['title'],
            'description': event['description'],
            'start_date': datetime.combine(event['event_date'], datetime.min.time()),
            'event_type': event['event_type'],
            'reference_uuid': event['reference_uuid'],
            'reference_name': event['reference_name']
        })
    
    return jsonify({'events': formatted_events})


@app.route('/edit/<int:event_id>', methods=['GET', 'POST'])
def edit_event(event_id):
    """Редактирование события"""
    event = db.get_event_by_id(event_id)
    
    if not event:
        flash('Событие не найдено!', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            event_date_str = request.form.get('event_date', '')
            is_active = request.form.get('is_active') == 'on'
            
            if not title or not event_date_str:
                flash('Название и дата обязательны!', 'error')
                return redirect(url_for('edit_event', event_id=event_id))
            
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
            
            db.update_event(
                event_id=event_id,
                title=title,
                description=description,
                event_date=event_date,
                is_active=is_active
            )
            
            flash('Событие обновлено!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Ошибка: {str(e)}', 'error')
    
    return render_template('edit_event.html', event=event)


@app.route('/delete/<int:event_id>')
def delete_event(event_id):
    """Удаление события"""
    if db.delete_event(event_id):
        flash('Событие удалено!', 'success')
    else:
        flash('Ошибка при удалении!', 'error')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Установите GRAPHQL_ENDPOINT через переменную окружения
    import os
    GRAPHQL_ENDPOINT = os.getenv('GRAPHQL_ENDPOINT')
    
    app.run(debug=True, host='0.0.0.0', port=5000)

