const API_URL = 'http://localhost:8000';

const taskForm = document.getElementById('task-form');
const taskInput = document.getElementById('task-input');
const taskList = document.getElementById('task-list');

// LocalStorage functions
function saveToLocalStorage(tasks) {
    localStorage.setItem('tasks', JSON.stringify(tasks));
}

function getFromLocalStorage() {
    const tasks = localStorage.getItem('tasks');
    return tasks ? JSON.parse(tasks) : [];
}

async function fetchTasks() {
    try {
        const response = await fetch(`${API_URL}/tasks`);
        const tasks = await response.json();
        saveToLocalStorage(tasks);
        renderTasks(tasks);
    } catch (error) {
        console.error('Failed to fetch from server, using local storage:', error);
        const localTasks = getFromLocalStorage();
        renderTasks(localTasks);
    }
}

async function addTask(text) {
    try {
        const response = await fetch(`${API_URL}/task`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        const newTask = await response.json();
        const tasks = [...getFromLocalStorage(), newTask];
        saveToLocalStorage(tasks);
        fetchTasks();
    } catch (error) {
        console.error('Failed to add task to server, saving locally:', error);
        const tasks = getFromLocalStorage();
        const newTask = {
            id: Date.now().toString(),
            text,
            completed: false
        };
        tasks.push(newTask);
        saveToLocalStorage(tasks);
        renderTasks(tasks);
    }
}

async function toggleTask(id, completed) {
    try {
        await fetch(`${API_URL}/task/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ completed })
        });
        fetchTasks();
    } catch (error) {
        console.error('Failed to update task on server, updating locally:', error);
        const tasks = getFromLocalStorage();
        const taskIndex = tasks.findIndex(t => t.id === id);
        if (taskIndex !== -1) {
            tasks[taskIndex].completed = completed;
            saveToLocalStorage(tasks);
            renderTasks(tasks);
        }
    }
}

async function deleteTask(id) {
    try {
        await fetch(`${API_URL}/task/${id}`, {
            method: 'DELETE'
        });
        fetchTasks();
    } catch (error) {
        console.error('Failed to delete task from server, removing locally:', error);
        const tasks = getFromLocalStorage().filter(t => t.id !== id);
        saveToLocalStorage(tasks);
        renderTasks(tasks);
    }
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
