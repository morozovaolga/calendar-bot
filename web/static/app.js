function switchTab(tabName, buttonEl) {
    // Скрыть все табы
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Показать выбранный таб
    document.getElementById(tabName).classList.add('active');
    if (buttonEl) {
        buttonEl.classList.add('active');
    }

    if (tabName === 'view') loadEvents();
    if (tabName === 'references') {
        // Сбрасываем выбор при переключении на вкладку ссылок
        document.getElementById('event-month-select').value = '';
        document.getElementById('event-select').innerHTML = '<option value="">-- Сначала выберите месяц --</option>';
        document.getElementById('event-select').disabled = true;
        document.getElementById('references-list').innerHTML = '';
    }
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
                const linksColor = e.references_count > 0 ? '#4caf50' : '#ff9800';
                const linksEmoji = e.references_count > 0 ? '✅' : '⚠️';
                const displayYear = e.year ? String(e.year) : '';
                const sanitizedTitle = e.title.replace(/'/g, "\\'");
                const sanitizedDescription = (e.description || '').replace(/'/g, "\\'");
                const sanitizedYear = displayYear.replace(/'/g, "\\'");
                row.innerHTML = `
                    <td>${e.event_date}</td>
                    <td><strong>${e.title}</strong></td>
                    <td>${(e.description || '').substring(0, 50)}${(e.description || '').length > 50 ? '...' : ''}</td>
                    <td>${displayYear}</td>
                    <td style="text-align: center; color: ${linksColor}; font-weight: bold;">
                        ${linksEmoji} ${e.references_count}
                    </td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn-edit" onclick="editEvent(${e.id}, '${sanitizedTitle}', '${sanitizedDescription}', '${sanitizedYear}')">✏️ Редактировать</button>
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
    const year = document.getElementById('year').value.trim();

    fetch('/api/events', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({day, month, title, event_type, description, year})
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

function editEvent(id, title, description, year) {
    document.getElementById('edit-id').value = id;
    document.getElementById('edit-title').value = title;
    document.getElementById('edit-description').value = description;
    document.getElementById('edit-year').value = year || '';
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
    const year = document.getElementById('edit-year').value.trim();

    fetch('/api/events/' + id, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({title, description, year})
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

function loadEventsByMonth() {
    const month = document.getElementById('event-month-select').value;
    const eventSelect = document.getElementById('event-select');

    if (!month) {
        eventSelect.innerHTML = '<option value="">-- Сначала выберите месяц --</option>';
        eventSelect.disabled = true;
        document.getElementById('references-list').innerHTML = '';
        return;
    }

    fetch('/api/events?month=' + month)
        .then(r => r.json())
        .then(data => {
            eventSelect.innerHTML = '<option value="">-- Выберите событие --</option>';
            if (data.events.length === 0) {
                eventSelect.innerHTML += '<option value="">Нет событий в этом месяце</option>';
            } else {
                data.events.forEach(e => {
                    const opt = document.createElement('option');
                    opt.value = e.id;
                    opt.textContent = `${e.event_date} - ${e.title}`;
                    eventSelect.appendChild(opt);
                });
            }
            eventSelect.disabled = false;
            document.getElementById('references-list').innerHTML = '';
        })
        .catch(err => {
            console.error(err);
            eventSelect.innerHTML = '<option value="">Ошибка загрузки</option>';
        });
}

function loadEventsForReferences() {
    // Эта функция больше не используется, но оставлена для совместимости
    loadEventsByMonth();
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
                                <button class="btn-edit" onclick="editReference(${ref.id}, '${ref.reference_type}', '${ref.reference_name.replace(/'/g, "\\'")}', '${(ref.reference_uuid || '').replace(/'/g, "\\'")}', '${(ref.reference_slug || '').replace(/'/g, "\\'")}', ${eventId})" style="padding: 5px 10px; font-size: 0.85em; background: #3b82f6; color: white; border: none; border-radius: 3px; cursor: pointer;">✏️ Редактировать</button>
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

function editReference(refId, refType, refName, refUuid, refSlug, eventId) {
    document.getElementById('edit-ref-id').value = refId;
    document.getElementById('edit-event-id').value = eventId;
    document.getElementById('edit-ref-type').value = refType;
    document.getElementById('edit-ref-name').value = refName;
    document.getElementById('edit-ref-uuid').value = refUuid || '';
    document.getElementById('edit-ref-slug').value = refSlug || '';
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
    const refSlug = document.getElementById('edit-ref-slug').value;

    fetch('/api/references/' + refId, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            reference_type: refType,
            reference_name: refName,
            reference_uuid: refUuid || '',
            reference_slug: refSlug || ''
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
    const refSlug = document.getElementById('ref-slug').value;

    fetch('/api/references', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            event_id: eventId,
            reference_type: refType,
            reference_name: refName,
            reference_uuid: refUuid || 'auto',
            reference_slug: refSlug || ''
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

