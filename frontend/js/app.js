// Main Application
class KanbanApp {
    constructor() {
        this.tasks = [];
        this.currentTask = null;
        this.taskFiles = new Map();
        this.draggedElement = null;
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
        this.setupFileUpload();
        
        // Connect WebSocket
        wsService.connect();
        wsService.on('*', (data) => this.handleWebSocketUpdate(data));
        
        // Load initial tasks
        await this.loadTasks();
    }

    setupEventListeners() {
        // Add Task Button
        document.getElementById('addTaskBtn').addEventListener('click', () => {
            this.openModal();
        });

        // Modal Close
        document.getElementById('modalClose').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('modalOverlay').addEventListener('click', () => {
            this.closeModal();
        });

        // Cancel Button
        document.getElementById('cancelBtn').addEventListener('click', () => {
            this.closeModal();
        });

        // Form Submit
        document.getElementById('taskForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveTask();
        });

        // Delete Task Button
        document.getElementById('deleteTaskBtn').addEventListener('click', () => {
            this.deleteCurrentTask();
        });

        // ESC key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    setupDragAndDrop() {
        const columns = document.querySelectorAll('.column-content');

        columns.forEach(column => {
            column.addEventListener('dragover', (e) => {
                e.preventDefault();
                column.classList.add('drag-over');
            });

            column.addEventListener('dragleave', () => {
                column.classList.remove('drag-over');
            });

            column.addEventListener('drop', (e) => {
                e.preventDefault();
                column.classList.remove('drag-over');
                
                if (this.draggedElement) {
                    const taskId = parseInt(this.draggedElement.dataset.taskId);
                    const newStatus = column.parentElement.dataset.status;
                    this.updateTaskStatus(taskId, newStatus);
                }
            });
        });
    }

    setupFileUpload() {
        const fileInput = document.getElementById('fileInput');
        const fileUploadArea = document.getElementById('fileUploadArea');

        fileInput.addEventListener('change', (e) => {
            this.handleFiles(e.target.files);
        });

        // Drag and drop for files
        fileUploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
            fileUploadArea.classList.add('drag-over');
        });

        fileUploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            e.stopPropagation();
            fileUploadArea.classList.remove('drag-over');
        });

        fileUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            e.stopPropagation();
            fileUploadArea.classList.remove('drag-over');
            this.handleFiles(e.dataTransfer.files);
        });
    }

    async loadTasks() {
        try {
            this.showLoading();
            const response = await api.getTasks();
            this.tasks = response.tasks || [];
            this.renderAllTasks();
            this.updateTaskCounts();
        } catch (error) {
            this.showToast('Ошибка загрузки задач', 'error');
            console.error('Failed to load tasks:', error);
        } finally {
            this.hideLoading();
        }
    }

    renderAllTasks() {
        // Clear all columns
        document.getElementById('todoColumn').innerHTML = '';
        document.getElementById('inProgressColumn').innerHTML = '';
        document.getElementById('doneColumn').innerHTML = '';

        // Render tasks by status
        this.tasks.forEach(task => {
            this.renderTask(task);
        });

        // Show empty states if needed
        this.updateEmptyStates();
    }

    renderTask(task) {
        const column = this.getColumnByStatus(task.status);
        if (!column) return;

        const taskCard = this.createTaskCard(task);
        column.appendChild(taskCard);
    }

    createTaskCard(task) {
        const card = document.createElement('div');
        card.className = 'task-card';
        card.draggable = true;
        card.dataset.taskId = task.id;

        card.addEventListener('dragstart', (e) => {
            this.draggedElement = card;
            card.classList.add('dragging');
        });

        card.addEventListener('dragend', () => {
            card.classList.remove('dragging');
            this.draggedElement = null;
        });

        card.addEventListener('click', () => {
            this.openModal(task.id);
        });

        const filesCount = task.files_count || 0;
        const createdDate = new Date(task.created_at).toLocaleDateString('ru-RU');

        card.innerHTML = `
            <div class="task-card-header">
                <h3 class="task-title">${this.escapeHtml(task.title)}</h3>
                <span class="task-id">#${task.id}</span>
            </div>
            ${task.description ? `<p class="task-description">${this.escapeHtml(task.description)}</p>` : ''}
            <div class="task-footer">
                <div class="task-meta">
                    ${filesCount > 0 ? `
                        <div class="task-files-count">
                            <i class="fas fa-paperclip"></i>
                            <span>${filesCount}</span>
                        </div>
                    ` : ''}
                    <div class="task-date">
                        <i class="fas fa-calendar"></i>
                        ${createdDate}
                    </div>
                </div>
            </div>
        `;

        return card;
    }

    getColumnByStatus(status) {
        const columnMap = {
            [TASK_STATUS.TODO]: document.getElementById('todoColumn'),
            [TASK_STATUS.IN_PROGRESS]: document.getElementById('inProgressColumn'),
            [TASK_STATUS.DONE]: document.getElementById('doneColumn')
        };
        return columnMap[status];
    }

    updateTaskCounts() {
        const counts = {
            todo: 0,
            in_progress: 0,
            done: 0
        };

        this.tasks.forEach(task => {
            counts[task.status]++;
        });

        Object.keys(counts).forEach(status => {
            const countEl = document.querySelector(`.task-count[data-status="${status}"]`);
            if (countEl) {
                countEl.textContent = counts[status];
            }
        });
    }

    updateEmptyStates() {
        const columns = [
            { id: 'todoColumn', status: 'todo' },
            { id: 'inProgressColumn', status: 'in_progress' },
            { id: 'doneColumn', status: 'done' }
        ];

        columns.forEach(({ id, status }) => {
            const column = document.getElementById(id);
            const hasTasks = this.tasks.some(task => task.status === status);
            
            if (!hasTasks) {
                column.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-inbox"></i>
                        <p>Нет задач</p>
                    </div>
                `;
            }
        });
    }

    async openModal(taskId = null) {
        this.currentTask = null;
        
        if (taskId) {
            try {
                this.showLoading();
                const task = await api.getTask(taskId);
                this.currentTask = task;
                await this.loadTaskFiles(taskId);
                this.fillModalForm(task);
                document.getElementById('deleteTaskBtn').style.display = 'block';
                document.getElementById('modalTitle').textContent = 'Редактировать задачу';
            } catch (error) {
                this.showToast('Ошибка загрузки задачи', 'error');
                return;
            } finally {
                this.hideLoading();
            }
        } else {
            this.clearModalForm();
            document.getElementById('deleteTaskBtn').style.display = 'none';
            document.getElementById('modalTitle').textContent = 'Новая задача';
        }

        document.getElementById('taskModal').classList.add('active');
    }

    closeModal() {
        document.getElementById('taskModal').classList.remove('active');
        this.clearModalForm();
        this.currentTask = null;
    }

    fillModalForm(task) {
        document.getElementById('taskId').value = task.id;
        document.getElementById('taskTitle').value = task.title;
        document.getElementById('taskDescription').value = task.description || '';
        document.getElementById('taskStatus').value = task.status;
    }

    clearModalForm() {
        document.getElementById('taskForm').reset();
        document.getElementById('taskId').value = '';
        document.getElementById('filesList').innerHTML = '';
    }

    async saveTask() {
        const taskId = document.getElementById('taskId').value;
        const title = document.getElementById('taskTitle').value.trim();
        const description = document.getElementById('taskDescription').value.trim();
        const status = document.getElementById('taskStatus').value;

        if (!title) {
            this.showToast('Название задачи обязательно', 'warning');
            return;
        }

        const taskData = {
            title,
            description: description || null,
            status
        };

        try {
            this.showLoading();

            let task;
            if (taskId) {
                task = await api.updateTask(parseInt(taskId), taskData);
                this.showToast('Задача обновлена', 'success');
            } else {
                task = await api.createTask(taskData);
                this.showToast('Задача создана', 'success');
            }

            // Upload files if any
            await this.uploadPendingFiles(task.id);

            await this.loadTasks();
            this.closeModal();
        } catch (error) {
            this.showToast('Ошибка сохранения задачи', 'error');
            console.error('Failed to save task:', error);
        } finally {
            this.hideLoading();
        }
    }

    async deleteCurrentTask() {
        if (!this.currentTask) return;

        if (!confirm('Вы уверены, что хотите удалить эту задачу?')) {
            return;
        }

        try {
            this.showLoading();
            await api.deleteTask(this.currentTask.id);
            this.showToast('Задача удалена', 'success');
            await this.loadTasks();
            this.closeModal();
        } catch (error) {
            this.showToast('Ошибка удаления задачи', 'error');
            console.error('Failed to delete task:', error);
        } finally {
            this.hideLoading();
        }
    }

    async updateTaskStatus(taskId, newStatus) {
        try {
            await api.updateTaskStatus(taskId, newStatus);
            
            // Update local state
            const task = this.tasks.find(t => t.id === taskId);
            if (task) {
                task.status = newStatus;
            }
            
            this.renderAllTasks();
            this.updateTaskCounts();
            this.showToast('Статус обновлен', 'success');
        } catch (error) {
            this.showToast('Ошибка обновления статуса', 'error');
            console.error('Failed to update task status:', error);
            await this.loadTasks(); // Reload to sync
        }
    }

    // File Management
    handleFiles(files) {
        const filesList = document.getElementById('filesList');
        
        Array.from(files).forEach(file => {
            if (file.size > FILE_CONFIG.MAX_SIZE) {
                this.showToast(`Файл ${file.name} слишком большой`, 'warning');
                return;
            }

            const fileItem = this.createFileItem(file);
            filesList.appendChild(fileItem);
        });
    }

    createFileItem(file, fileData = null) {
        const div = document.createElement('div');
        div.className = 'file-item';
        
        const isUploaded = !!fileData;
        const fileSize = this.formatFileSize(file.size || fileData?.size_bytes);
        
        div.innerHTML = `
            <div class="file-info">
                <i class="fas fa-file"></i>
                <span class="file-name">${this.escapeHtml(file.name || fileData.filename)}</span>
                <span class="file-size">${fileSize}</span>
            </div>
            <div class="file-actions">
                ${isUploaded ? `
                    <button type="button" class="file-action-btn download" data-file-id="${fileData.id}">
                        <i class="fas fa-download"></i>
                    </button>
                ` : ''}
                <button type="button" class="file-action-btn delete">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Store file reference if not uploaded yet
        if (!isUploaded) {
            div.dataset.file = file.name;
            div._file = file;
        }

        // Delete button
        div.querySelector('.delete').addEventListener('click', async () => {
            if (isUploaded) {
                if (confirm('Удалить файл?')) {
                    try {
                        await api.deleteFile(fileData.id);
                        div.remove();
                        this.showToast('Файл удален', 'success');
                    } catch (error) {
                        this.showToast('Ошибка удаления файла', 'error');
                    }
                }
            } else {
                div.remove();
            }
        });

        // Download button
        if (isUploaded) {
            div.querySelector('.download').addEventListener('click', async () => {
                try {
                    await api.downloadFile(fileData.id);
                    this.showToast('Скачивание началось', 'success');
                } catch (error) {
                    this.showToast('Ошибка скачивания', 'error');
                }
            });
        }

        return div;
    }

    async loadTaskFiles(taskId) {
        try {
            const response = await api.getFilesByTask(taskId);
            const filesList = document.getElementById('filesList');
            filesList.innerHTML = '';
            
            if (response.files && response.files.length > 0) {
                response.files.forEach(fileData => {
                    const fileItem = this.createFileItem({ name: fileData.filename, size: fileData.size_bytes }, fileData);
                    filesList.appendChild(fileItem);
                });
            }
        } catch (error) {
            console.error('Failed to load files:', error);
        }
    }

    async uploadPendingFiles(taskId) {
        const filesList = document.getElementById('filesList');
        const pendingFiles = filesList.querySelectorAll('.file-item[data-file]');
        
        for (const fileItem of pendingFiles) {
            const file = fileItem._file;
            if (file) {
                try {
                    await api.uploadFile(file, taskId);
                } catch (error) {
                    console.error('Failed to upload file:', error);
                    this.showToast(`Ошибка загрузки ${file.name}`, 'error');
                }
            }
        }
    }

    // WebSocket Handler
    async handleWebSocketUpdate(data) {
        console.log('WebSocket update:', data);
        
        // Reload tasks on any update from other clients
        await this.loadTasks();
        
        const action = data.action || data.event;
        if (action === 'task_created') {
            this.showToast('Новая задача создана', 'success');
        } else if (action === 'task_updated') {
            this.showToast('Задача обновлена', 'success');
        } else if (action === 'task_deleted') {
            this.showToast('Задача удалена', 'success');
        }
    }

    // Utilities
    showLoading() {
        document.getElementById('loadingOverlay').classList.add('active');
    }

    hideLoading() {
        document.getElementById('loadingOverlay').classList.remove('active');
    }

    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const iconMap = {
            success: 'fa-check-circle',
            error: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle'
        };
        
        toast.innerHTML = `
            <i class="fas ${iconMap[type]}"></i>
            <span class="toast-message">${message}</span>
        `;
        
        document.getElementById('toastContainer').appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, UI_CONFIG.TOAST_DURATION);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.kanbanApp = new KanbanApp();
});
