#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Веб-интерфейс для управления литературным календарём
Flask приложение для добавления, редактирования и удаления событий
"""

from flask import Flask, render_template_string, request, jsonify, redirect, url_for
from literary_calendar_database import LiteraryCalendarDatabase
import json
from datetime import datetime

app = Flask(__name__)
db_path = 'literary_events.db'

# HTML шаблон
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📚 Редактор Литературного Календаря</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { opacity: 0.9; }
        .content {
            padding: 30px;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            border-bottom: 2px solid #eee;
        }
        .tab-btn {
            padding: 12px 24px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1em;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        .tab-btn.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        .tab-btn:hover {
            color: #667eea;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        input, textarea, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 1em;
            font-family: inherit;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        textarea {
            resize: vertical;
            min-height: 100px;
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        button {
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
        }
        .btn-secondary:hover {
            background: #e0e0e0;
        }
        .btn-danger {
            background: #ef4444;
            color: white;
        }
        .btn-danger:hover {
            background: #dc2626;
        }
        .events-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        .events-table th {
            background: #f0f0f0;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #ddd;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        .modal.active {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .modal-content {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            width: 90%;
            max-width: 600px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #eee;
        }
        .modal-header h2 {
            margin: 0;
        }
        .close-btn {
            background: none;
            border: none;
            font-size: 1.5em;
            cursor: pointer;
            color: #666;
        }
        .close-btn:hover {
            color: #000;
        }
        .btn-edit {
            background: #3b82f6;
            color: white;
            padding: 8px 16px;
            font-size: 0.9em;
        }
        .btn-edit:hover {
            background: #2563eb;
        }
        .btn-delete {
            background: #ef4444;
            color: white;
            padding: 8px 16px;
            font-size: 0.9em;
            margin-left: 5px;
        }
        .btn-delete:hover {
            background: #dc2626;
        }
        .action-buttons {
            display: flex;
            gap: 5px;
        }
        .events-table td {
            padding: 15px;
            border-bottom: 1px solid #ddd;
        }
        .events-table tr:hover {
            background: #f9f9f9;
        }
        .event-actions {
            display: flex;
            gap: 10px;
        }
        .btn-small {
            padding: 6px 12px;
            font-size: 0.9em;
        }
        .alert {
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .alert-success {
            background: #d1fae5;
            color: #065f46;
            border: 1px solid #a7f3d0;
        }
        .alert-error {
            background: #fee2e2;
            color: #991b1b;
            border: 1px solid #fecaca;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .stat-label {
            opacity: 0.9;
        }
        .search-box {
            margin-bottom: 20px;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.4);
        }
        .modal.active {
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .modal-content {
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            width: 90%;
            max-width: 500px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        .close-modal {
            cursor: pointer;
            float: right;
            font-size: 2em;
            font-weight: bold;
            color: #aaa;
        }
        .close-modal:hover {
            color: #000;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 Литературный Календарь 2025</h1>
            <p>Веб-интерфейс для управления событиями и ссылками на книги</p>
        </div>
        
        <div class="content">
            <div id="message"></div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value" id="total-events">0</div>
                    <div class="stat-label">Всего событий</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="today-events">0</div>
                    <div class="stat-label">Событий сегодня</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="total-references">0</div>
                    <div class="stat-label">Ссылок на книги</div>
                </div>
            </div>
            
            <div class="tabs">
                <button class="tab-btn active" onclick="switchTab('view')">📖 Просмотр</button>
                <button class="tab-btn" onclick="switchTab('add')">➕ Добавить</button>
                <button class="tab-btn" onclick="switchTab('references')">🔗 Ссылки на книги</button>
            </div>
            
            <!-- Таб Просмотр -->
            <div id="view" class="tab-content active">
                <div class="search-box">
                    <input type="text" id="search" placeholder="🔍 Поиск по названию события..." 
                           onkeyup="searchEvents()" style="max-width: 100%;">
                </div>
                <table class="events-table">
                    <thead>
                        <tr>
                            <th>📅 Дата</th>
                            <th>📝 Название</th>
                            <th>✏️ Описание</th>
                            <th>🔗 Ссылки</th>
                            <th>⚙️ Действия</th>
                        </tr>
                    </thead>
                    <tbody id="events-table-body">
                    </tbody>
                </table>
            </div>
            
            <!-- Таб Добавление -->
            <div id="add" class="tab-content">
                <h2>➕ Добавить новое событие</h2>
                <form onsubmit="addEvent(event)">
                    <div class="form-row">
                        <div class="form-group">
                            <label for="day">День (1-31)</label>
                            <input type="number" id="day" min="1" max="31" required>
                        </div>
                        <div class="form-group">
                            <label for="month">Месяц</label>
                            <select id="month" required>
                                <option value="">Выберите месяц</option>
                                <option value="1">Январь</option>
                                <option value="2">Февраль</option>
                                <option value="3">Март</option>
                                <option value="4">Апрель</option>
                                <option value="5">Май</option>
                                <option value="6">Июнь</option>
                                <option value="7">Июль</option>
                                <option value="8">Август</option>
                                <option value="9">Сентябрь</option>
                                <option value="10">Октябрь</option>
                                <option value="11">Ноябрь</option>
                                <option value="12">Декабрь</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="title">Название события *</label>
                        <input type="text" id="title" placeholder="Например: День рождения А.С. Пушкина" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="event_type">Тип события</label>
                        <select id="event_type">
                            <option value="литературное событие">Литературное событие</option>
                            <option value="день рождения">День рождения</option>
                            <option value="смерти">День смерти</option>
                            <option value="юбилей">Юбилей</option>
                            <option value="памятная дата">Памятная дата</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="description">Описание</label>
                        <textarea id="description" placeholder="Краткое описание события..."></textarea>
                    </div>
                    
                    <button type="submit" class="btn-primary">✅ Добавить событие</button>
                </form>
            </div>
            
            <!-- Таб Ссылки -->
            <div id="references" class="tab-content">
                <h2>🔗 Управление ссылками на книги</h2>
                <p>Выберите событие и добавьте ссылку на книгу или автора:</p>
                
                <div class="form-group">
                    <label for="event-select">Выберите событие</label>
                    <select id="event-select" onchange="loadEventReferences()">
                        <option value="">-- Выберите событие --</option>
                    </select>
                </div>
                
                <div id="references-list"></div>
                
                <h3 style="margin-top: 30px;">➕ Добавить новую ссылку</h3>
                <form onsubmit="addReference(event)">
                    <div class="form-group">
                        <label for="ref-type">Тип ссылки</label>
                        <select id="ref-type" required>
                            <option value="author">Автор</option>
                            <option value="book">Книга</option>
                            <option value="tag">Тег</option>
                            <option value="category">Категория</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="ref-name">Название/Имя *</label>
                        <input type="text" id="ref-name" placeholder="Например: А.С. Пушкин" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="ref-uuid">UUID (опционально)</label>
                        <input type="text" id="ref-uuid" placeholder="author-123">
                    </div>
                    
                    <button type="submit" class="btn-primary">🔗 Добавить ссылку</button>
                </form>
            </div>
        </div>
    </div>
    
    <!-- Модальное окно для редактирования события -->
    <div id="editModal" class="modal" onclick="if(event.target === this) closeModal()">
        <div class="modal-content">
            <div class="modal-header">
                <h2>✏️ Редактировать событие</h2>
                <button type="button" class="close-btn" onclick="closeModal()">&times;</button>
            </div>
            <form onsubmit="updateEvent(event)">
                <input type="hidden" id="edit-id">
                <div class="form-group">
                    <label for="edit-title">Название</label>
                    <input type="text" id="edit-title" required>
                </div>
                <div class="form-group">
                    <label for="edit-description">Описание</label>
                    <textarea id="edit-description"></textarea>
                </div>
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button type="submit" class="btn-primary">💾 Сохранить</button>
                    <button type="button" class="btn-secondary" onclick="closeModal()">Отмена</button>
                </div>
            </form>
        </div>
    </div>
    
    <!-- Модальное окно для редактирования ссылки -->
    <div id="referenceModal" class="modal" onclick="if(event.target === this) closeReferenceModal()">
        <div class="modal-content">
            <div class="modal-header">
                <h2>✏️ Редактировать ссылку</h2>
                <button type="button" class="close-btn" onclick="closeReferenceModal()">&times;</button>
            </div>
            <form onsubmit="updateReference(event)">
                <input type="hidden" id="edit-ref-id">
                <input type="hidden" id="edit-event-id">
                <div class="form-group">
                    <label for="edit-ref-type">Тип ссылки</label>
                    <select id="edit-ref-type" required>
                        <option value="author">Автор</option>
                        <option value="book">Книга</option>
                        <option value="tag">Тег</option>
                        <option value="category">Категория</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="edit-ref-name">Название/Имя</label>
                    <input type="text" id="edit-ref-name" required>
                </div>
                <div class="form-group">
                    <label for="edit-ref-uuid">UUID</label>
                    <input type="text" id="edit-ref-uuid" placeholder="Опционально">
                </div>
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button type="submit" class="btn-primary">💾 Сохранить</button>
                    <button type="button" class="btn-secondary" onclick="closeReferenceModal()">Отмена</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        function switchTab(tabName) {
            // Скрыть все табы
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Показать выбранный таб
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            if (tabName === 'view') loadEvents();
            if (tabName === 'references') loadEventsForReferences();
        }
        
        function showMessage(text, type = 'success') {
            const msg = document.getElementById('message');
            msg.innerHTML = '<div class="alert alert-' + type + '">' + text + '</div>';
            setTimeout(() => { msg.innerHTML = ''; }, 5000);
        }
        
        function loadEvents() {
            fetch('/api/events')
                .then(r => r.json())
                .then(data => {
                    const tbody = document.getElementById('events-table-body');
                    tbody.innerHTML = '';
                    data.events.forEach(e => {
                        const row = tbody.insertRow();
                        // Определяем цвет для столбца ссылок
                        const linksColor = e.references_count > 0 ? '#4caf50' : '#ff9800';
                        const linksEmoji = e.references_count > 0 ? '✅' : '⚠️';
                        row.innerHTML = `
                            <td>${e.event_date}</td>
                            <td><strong>${e.title}</strong></td>
                            <td>${(e.description || '').substring(0, 50)}${(e.description || '').length > 50 ? '...' : ''}</td>
                            <td style="text-align: center; color: ${linksColor}; font-weight: bold;">
                                ${linksEmoji} ${e.references_count}
                            </td>
                            <td>
                                <div class="action-buttons">
                                    <button class="btn-edit" onclick="editEvent(${e.id}, '${e.title.replace(/'/g, "\\'")}', '${(e.description || '').replace(/'/g, "\\'")}', '${e.event_date}')">✏️ Редактировать</button>
                                    <button class="btn-delete" onclick="deleteEvent(${e.id})">🗑️ Удалить</button>
                                </div>
                            </td>
                        `;
                    });
                    
                    document.getElementById('total-events').textContent = data.stats.total_events;
                    document.getElementById('today-events').textContent = data.stats.today_events;
                    document.getElementById('total-references').textContent = data.stats.total_references;
                })
                .catch(err => showMessage('Ошибка: ' + err, 'error'));
        }
        
        function searchEvents() {
            const query = document.getElementById('search').value.toLowerCase();
            document.querySelectorAll('.events-table tbody tr').forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        }
        
        function addEvent(e) {
            e.preventDefault();
            const day = document.getElementById('day').value;
            const month = document.getElementById('month').value;
            const title = document.getElementById('title').value;
            const event_type = document.getElementById('event_type').value;
            const description = document.getElementById('description').value;
            
            fetch('/api/events', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({day, month, title, event_type, description})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showMessage('✅ Событие добавлено!', 'success');
                    e.target.reset();
                    loadEvents();
                } else {
                    showMessage('❌ Ошибка: ' + data.message, 'error');
                }
            })
            .catch(err => showMessage('Ошибка: ' + err, 'error'));
        }
        
        function editEvent(id, title, description) {
            document.getElementById('edit-id').value = id;
            document.getElementById('edit-title').value = title;
            document.getElementById('edit-description').value = description;
            document.getElementById('editModal').classList.add('active');
        }
        
        function closeModal() {
            document.getElementById('editModal').classList.remove('active');
        }
        
        function updateEvent(e) {
            e.preventDefault();
            const id = document.getElementById('edit-id').value;
            const title = document.getElementById('edit-title').value;
            const description = document.getElementById('edit-description').value;
            
            fetch('/api/events/' + id, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({title, description})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showMessage('✅ Событие обновлено!', 'success');
                    closeModal();
                    loadEvents();
                } else {
                    showMessage('❌ Ошибка: ' + data.message, 'error');
                }
            })
            .catch(err => showMessage('Ошибка: ' + err, 'error'));
        }
        
        function deleteEvent(id) {
            if (confirm('Вы уверены? Это действие нельзя отменить.')) {
                fetch('/api/events/' + id, {method: 'DELETE'})
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) {
                            showMessage('✅ Событие удалено!', 'success');
                            loadEvents();
                        }
                    })
                    .catch(err => showMessage('Ошибка: ' + err, 'error'));
            }
        }
        
        function loadEventsForReferences() {
            fetch('/api/events')
                .then(r => r.json())
                .then(data => {
                    const select = document.getElementById('event-select');
                    select.innerHTML = '<option value="">-- Выберите событие --</option>';
                    data.events.forEach(e => {
                        const opt = document.createElement('option');
                        opt.value = e.id;
                        opt.textContent = e.title;
                        select.appendChild(opt);
                    });
                })
                .catch(err => console.error(err));
        }
        
        function loadEventReferences() {
            const eventId = document.getElementById('event-select').value;
            if (!eventId) return;
            
            fetch('/api/events/' + eventId + '/references')
                .then(r => r.json())
                .then(data => {
                    const refList = document.getElementById('references-list');
                    refList.innerHTML = '<h4>Текущие ссылки:</h4>';
                    if (data.references.length === 0) {
                        refList.innerHTML += '<p style="color: #999;">Нет ссылок</p>';
                    } else {
                        refList.innerHTML += '<table style="width: 100%; border-collapse: collapse;">';
                        refList.innerHTML += '<tr style="border-bottom: 2px solid #ddd;"><th style="text-align: left; padding: 10px;">Тип</th><th style="text-align: left; padding: 10px;">Название</th><th style="text-align: center; padding: 10px;">Действия</th></tr>';
                        data.references.forEach(ref => {
                            refList.innerHTML += `
                                <tr style="border-bottom: 1px solid #ddd;">
                                    <td style="padding: 10px;"><strong>${ref.reference_type}</strong></td>
                                    <td style="padding: 10px;">${ref.reference_name}</td>
                                    <td style="padding: 10px; text-align: center; display: flex; gap: 5px; justify-content: center;">
                                        <button class="btn-edit" onclick="editReference(${ref.id}, '${ref.reference_type}', '${ref.reference_name.replace(/'/g, "\\'")}', '${(ref.reference_uuid || '').replace(/'/g, "\\'")}', ${eventId})" style="padding: 5px 10px; font-size: 0.85em; background: #3b82f6; color: white; border: none; border-radius: 3px; cursor: pointer;">✏️ Редактировать</button>
                                        <button class="btn-delete" onclick="deleteReference(${ref.id}, ${eventId})" style="padding: 5px 10px; font-size: 0.85em; background: #ef4444; color: white; border: none; border-radius: 3px; cursor: pointer;">🗑️ Удалить</button>
                                    </td>
                                </tr>
                            `;
                        });
                        refList.innerHTML += '</table>';
                    }
                })
                .catch(err => console.error(err));
        }
        
        function editReference(refId, refType, refName, refUuid, eventId) {
            document.getElementById('edit-ref-id').value = refId;
            document.getElementById('edit-event-id').value = eventId;
            document.getElementById('edit-ref-type').value = refType;
            document.getElementById('edit-ref-name').value = refName;
            document.getElementById('edit-ref-uuid').value = refUuid;
            document.getElementById('referenceModal').classList.add('active');
        }
        
        function closeReferenceModal() {
            document.getElementById('referenceModal').classList.remove('active');
        }
        
        function updateReference(e) {
            e.preventDefault();
            const refId = document.getElementById('edit-ref-id').value;
            const eventId = document.getElementById('edit-event-id').value;
            const refType = document.getElementById('edit-ref-type').value;
            const refName = document.getElementById('edit-ref-name').value;
            const refUuid = document.getElementById('edit-ref-uuid').value;
            
            fetch('/api/references/' + refId, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    reference_type: refType,
                    reference_name: refName,
                    reference_uuid: refUuid
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showMessage('✅ Ссылка обновлена!', 'success');
                    closeReferenceModal();
                    loadEventReferences();
                    loadEvents();
                } else {
                    showMessage('❌ Ошибка: ' + data.error, 'error');
                }
            })
            .catch(err => showMessage('Ошибка: ' + err, 'error'));
        }
        
        function deleteReference(refId, eventId) {
            if (confirm('Удалить эту ссылку?')) {
                fetch('/api/references/' + refId, {method: 'DELETE'})
                    .then(r => r.json())
                    .then(data => {
                        if (data.success) {
                            showMessage('✅ Ссылка удалена!', 'success');
                            loadEventReferences();
                            loadEvents();
                        }
                    })
                    .catch(err => showMessage('Ошибка: ' + err, 'error'));
            }
        }
        
        function addReference(e) {
            e.preventDefault();
            const eventId = document.getElementById('event-select').value;
            if (!eventId) {
                showMessage('❌ Выберите событие', 'error');
                return;
            }
            
            const refType = document.getElementById('ref-type').value;
            const refName = document.getElementById('ref-name').value;
            const refUuid = document.getElementById('ref-uuid').value;
            
            fetch('/api/references', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    event_id: eventId,
                    reference_type: refType,
                    reference_name: refName,
                    reference_uuid: refUuid || 'auto'
                })
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showMessage('✅ Ссылка добавлена!', 'success');
                    e.target.reset();
                    loadEventReferences();
                } else {
                    showMessage('❌ Ошибка: ' + data.message, 'error');
                }
            })
            .catch(err => showMessage('Ошибка: ' + err, 'error'));
        }
        
        // Загрузить события при открытии
        window.addEventListener('load', () => {
            loadEvents();
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/events', methods=['GET', 'POST'])
def api_events():
    if request.method == 'GET':
        try:
            db = LiteraryCalendarDatabase(db_path)
            conn = db.conn
            c = conn.cursor()
            
            # Получаем все события
            c.execute('SELECT id, event_date, title, description FROM events ORDER BY event_date')
            events = []
            for row in c.fetchall():
                event_id = row[0]
                # Подсчитываем ссылки для этого события
                c.execute('SELECT COUNT(*) FROM event_references WHERE event_id = ?', (event_id,))
                refs_count = c.fetchone()[0]
                
                events.append({
                    'id': event_id,
                    'event_date': row[1],
                    'title': row[2],
                    'description': row[3],
                    'references_count': refs_count
                })
            
            # Статистика
            c.execute('SELECT COUNT(*) FROM events')
            total_events = c.fetchone()[0]
            
            today = datetime.now()
            today_str = f"{today.month:02d}-{today.day:02d}"
            c.execute('SELECT COUNT(*) FROM events WHERE event_date = ?', (today_str,))
            today_events = c.fetchone()[0]
            
            c.execute('SELECT COUNT(*) FROM event_references')
            total_references = c.fetchone()[0]
            
            db.close()
            
            return jsonify({
                'events': events,
                'stats': {
                    'total_events': total_events,
                    'today_events': today_events,
                    'total_references': total_references
                }
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.json
            db = LiteraryCalendarDatabase(db_path)
            
            event_id = db.add_event(
                month=int(data['month']),
                day=int(data['day']),
                event_type=data.get('event_type', 'литературное событие'),
                title=data['title'],
                description=data.get('description', ''),
                author_name='',
                book_title='',
                year=''
            )
            
            db.close()
            return jsonify({'success': True, 'id': event_id})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/events/<int:event_id>', methods=['GET', 'PUT', 'DELETE'])
def api_event(event_id):
    try:
        db = LiteraryCalendarDatabase(db_path)
        conn = db.conn
        c = conn.cursor()
        
        if request.method == 'GET':
            c.execute('SELECT * FROM events WHERE id = ?', (event_id,))
            event = c.fetchone()
            db.close()
            if event:
                return jsonify(dict(zip(['id', 'event_date', 'title', 'description', 'author_name', 'book_title', 'year'], event)))
            return jsonify({'error': 'Not found'}), 404
        
        elif request.method == 'PUT':
            data = request.json
            c.execute('UPDATE events SET title = ?, description = ? WHERE id = ?',
                     (data['title'], data.get('description', ''), event_id))
            conn.commit()
            db.close()
            return jsonify({'success': True})
        
        elif request.method == 'DELETE':
            c.execute('DELETE FROM events WHERE id = ?', (event_id,))
            conn.commit()
            db.close()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events/<int:event_id>/references', methods=['GET'])
def api_event_references(event_id):
    try:
        db = LiteraryCalendarDatabase(db_path)
        conn = db.conn
        c = conn.cursor()
        
        c.execute('SELECT * FROM event_references WHERE event_id = ?', (event_id,))
        references = [dict(zip(['id', 'event_id', 'reference_type', 'reference_uuid', 'reference_slug', 'reference_name', 'priority', 'metadata'], row)) 
                     for row in c.fetchall()]
        
        db.close()
        return jsonify({'references': references})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/references', methods=['POST'])
def api_add_reference():
    try:
        data = request.json
        db = LiteraryCalendarDatabase(db_path)
        
        ref_uuid = data['reference_uuid']
        if ref_uuid == 'auto':
            ref_uuid = f"{data['reference_type']}-{data['reference_name'].lower().replace(' ', '-')}"
        
        db.add_reference(
            event_id=int(data['event_id']),
            reference_type=data['reference_type'],
            reference_uuid=ref_uuid,
            reference_slug=ref_uuid.lower(),
            reference_name=data['reference_name'],
            priority=1
        )
        
        db.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/references/<int:ref_id>', methods=['DELETE', 'PUT'])
def api_delete_or_update_reference(ref_id):
    try:
        db = LiteraryCalendarDatabase(db_path)
        conn = db.conn
        c = conn.cursor()
        
        if request.method == 'DELETE':
            c.execute('DELETE FROM event_references WHERE id = ?', (ref_id,))
            conn.commit()
            db.close()
            return jsonify({'success': True})
        
        elif request.method == 'PUT':
            data = request.json
            c.execute('''UPDATE event_references 
                         SET reference_type = ?, reference_name = ?, reference_uuid = ?, reference_slug = ?
                         WHERE id = ?''',
                     (data['reference_type'], data['reference_name'], 
                      data.get('reference_uuid', ''), 
                      data.get('reference_uuid', '').lower(), 
                      ref_id))
            conn.commit()
            db.close()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Запуск веб-интерфейса редактора календаря...")
    print("📍 Откройте: http://localhost:5000")
    print("✅ Для остановки нажмите Ctrl+C\n")
    app.run(debug=True, host='localhost', port=5000)
