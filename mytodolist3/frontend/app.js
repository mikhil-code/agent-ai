const API_URL = 'http://localhost:8000';

const taskForm = document.getElementById('task-form');
const taskInput = document.getElementById('task-input');
const taskList = document.getElementById('task-list');

async function fetchTasks() {
    const response = await fetch(`${API_URL}/tasks`);
    const tasks = await response.json();
    renderTasks(tasks);
}

async function addTask(text) {
    await fetch(`${API_URL}/task`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    });
    fetchTasks();
}

async function toggleTask(id, completed) {
    await fetch(`${API_URL}/task/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed })
    });
    fetchTasks();
}

async function deleteTask(id) {
    await fetch(`${API_URL}/task/${id}`, {
        method: 'DELETE'
    });
    fetchTasks();
}

function renderTasks(tasks) {
    taskList.innerHTML = tasks.map(task => `
        <li class="task-item ${task.completed ? 'completed' : ''}">
            <input type="checkbox" 
                   ${task.completed ? 'checked' : ''} 
                   onchange="toggleTask('${task.id}', this.checked)">
            <span>${task.text}</span>
            <button onclick="deleteTask('${task.id}')">Delete</button>
        </li>
    `).join('');
}

taskForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = taskInput.value.trim();
    if (text) {
        addTask(text);
        taskInput.value = '';
    }
});

// Initial load
fetchTasks();
