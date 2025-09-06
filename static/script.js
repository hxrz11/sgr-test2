let currentResults = null;

function escape(str) {
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function formatSQL(sql) {
    return sql
        .replace(/\s+/g, ' ')
        .replace(/SELECT\s/gi, 'SELECT\n  ')
        .replace(/FROM/gi, '\nFROM')
        .replace(/WHERE/gi, '\nWHERE')
        .replace(/GROUP BY/gi, '\nGROUP BY')
        .replace(/ORDER BY/gi, '\nORDER BY')
        .replace(/LIMIT/gi, '\nLIMIT')
        .replace(/JOIN/gi, '\nJOIN')
        .replace(/AND/gi, '\n  AND')
        .replace(/OR/gi, '\n  OR')
        .replace(/,\s*/g, ',\n  ')
        .trim();
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', async function() {
    await checkModelsAvailability();
    await loadHistory();
});

// Проверка доступности моделей
async function checkModelsAvailability() {
    try {
        const response = await fetch('/api/models');
        const data = await response.json();
        
        const select = document.getElementById('model-select');
        const status = document.getElementById('model-status');
        
        // Обновляем статус текущей модели
        const currentModel = select.value;
        const modelInfo = data.models.find(m => m.name === currentModel);
        
        if (modelInfo && modelInfo.available) {
            status.textContent = '✅ Доступна';
            status.className = 'status-available';
        } else {
            status.textContent = '❌ Недоступна';
            status.className = 'status-unavailable';
        }
        
    } catch (error) {
        console.error('Ошибка проверки моделей:', error);
    }
}

// Смена модели
document.getElementById('model-select').addEventListener('change', checkModelsAvailability);

// Отправка запроса
async function submitQuery() {
    const question = document.getElementById('question').value.trim();
    if (!question) {
        alert('Введите вопрос');
        return;
    }
    
    const model = document.getElementById('model-select').value;
    
    // Показываем загрузку
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    document.getElementById('submit-btn').disabled = true;
    
    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                model: model
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        result.question = question;
        result.timestamp = new Date().toISOString();
        result.raw_response = result.results;
        currentResults = result;
        displayResults(result);
        await loadHistory();
        
    } catch (error) {
        alert(`Ошибка: ${error.message}`);
        console.error('Ошибка запроса:', error);
    } finally {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('submit-btn').disabled = false;
    }
}

// Отображение результатов
function displayResults(result) {
    document.getElementById('explanation-text').textContent = result.explanation;

    const confidence = Math.round(result.confidence * 100);
    document.getElementById('confidence-fill').style.width = `${confidence}%`;
    document.getElementById('confidence-text').textContent = `${confidence}%`;

    document.getElementById('sql-query').textContent = formatSQL(result.sql_query);

    const dt = result.timestamp ? new Date(result.timestamp) : new Date();
    const statsHtml = `
        <p><strong>Дата:</strong> ${dt.toLocaleDateString()}</p>
        <p><strong>Время:</strong> ${dt.toLocaleTimeString()}</p>
        <p><strong>Запрос пользователя:</strong> ${escape(result.question || '')}</p>
        <p><strong>Найдено записей:</strong> ${result.results.length}</p>
        <p><strong>Время выполнения:</strong> ${result.execution_time_ms} мс</p>
        <p><strong>Модель:</strong> ${result.model_used}</p>
    `;
    document.getElementById('data-stats').innerHTML = statsHtml;

    const raw = result.raw_response || result.results;
    document.getElementById('raw-response').textContent = JSON.stringify(raw, null, 2);
    
    // Таблица данных
    if (result.results.length > 0) {
        const table = createDataTable(result.results);
        document.getElementById('data-table').innerHTML = table;
    } else {
        document.getElementById('data-table').innerHTML = '<p>Данные не найдены</p>';
    }
    
    // Показываем результаты
    document.getElementById('results').style.display = 'block';
    showTab('explanation', null);
}

// Создание таблицы данных
function createDataTable(data) {
    if (data.length === 0) return '<p>Нет данных</p>';
    
    const headers = Object.keys(data[0]);
    const maxRows = Math.min(data.length, 20); // Ограничиваем до 20 строк
    
    let html = '<div class="data-table"><table><thead><tr>';
    headers.forEach(header => {
        html += `<th>${header}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    for (let i = 0; i < maxRows; i++) {
        const row = data[i];
        html += '<tr>';
        headers.forEach(header => {
            let value = row[header];
            if (value === null || value === undefined) {
                value = '-';
            } else if (typeof value === 'string' && value.length > 50) {
                value = value.substring(0, 47) + '...';
            }
            html += `<td>${escape(value)}</td>`;
        });
        html += '</tr>';
    }
    
    html += '</tbody></table></div>';
    
    if (data.length > maxRows) {
        html += `<p><em>Показано ${maxRows} из ${data.length} записей</em></p>`;
    }
    
    return html;
}

// Переключение табов
function showTab(tabName, e) {
    // Скрываем все табы
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.style.display = 'none');

    // Убираем активность с кнопок
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => btn.classList.remove('active'));

    // Показываем нужный таб
    document.getElementById(`${tabName}-tab`).style.display = 'block';

    if (e) {
        e.target.classList.add('active');
    } else {
        const btn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
        if (btn) {
            btn.classList.add('active');
        }
    }
}

// Копирование SQL
function copySql() {
    const sql = document.getElementById('sql-query').textContent;
    navigator.clipboard.writeText(sql).then(() => {
        alert('SQL запрос скопирован в буфер обмена');
    }).catch(err => {
        console.error('Ошибка копирования:', err);
    });
}

async function loadHistory() {
    try {
        const response = await fetch('/api/history');
        const data = await response.json();
        const list = document.getElementById('history-list');
        list.innerHTML = '';
        data.logs.forEach(log => {
            const btn = document.createElement('button');
            btn.textContent = log.question;
            btn.onclick = () => {
                currentResults = log;
                displayResults(log);
            };
            list.appendChild(btn);
        });
    } catch (error) {
        console.error('Ошибка загрузки истории:', error);
    }
}

// Обработка Enter в textarea
document.getElementById('question').addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        submitQuery();
    }
});
