// API Configuration
const API_CONFIG = {
    BOARD_SERVICE: 'http://localhost:8000',
    FILE_SERVICE: 'http://localhost:8001',
    WS_URL: 'ws://localhost:8000/ws'
};

// API Endpoints
const ENDPOINTS = {
    TASKS: {
        LIST: '/api/v1/tasks',
        CREATE: '/api/v1/tasks',
        GET: (id) => `/api/v1/tasks/${id}`,
        UPDATE: (id) => `/api/v1/tasks/${id}`,
        DELETE: (id) => `/api/v1/tasks/${id}`,
        UPDATE_STATUS: (id) => `/api/v1/tasks/${id}/status`
    },
    FILES: {
        UPLOAD: '/api/v1/files/upload',
        GET: (id) => `/api/v1/files/${id}`,
        DOWNLOAD: (id) => `/api/v1/files/${id}/download`,
        DELETE: (id) => `/api/v1/files/${id}`,
        BY_TASK: (taskId) => `/api/v1/files/task/${taskId}`
    }
};

// Task Status Configuration
const TASK_STATUS = {
    TODO: 'todo',
    IN_PROGRESS: 'in_progress',
    DONE: 'done'
};

const STATUS_LABELS = {
    [TASK_STATUS.TODO]: 'К выполнению',
    [TASK_STATUS.IN_PROGRESS]: 'В процессе',
    [TASK_STATUS.DONE]: 'Завершено'
};

// File Configuration
const FILE_CONFIG = {
    MAX_SIZE: 50 * 1024 * 1024, // 50MB
    ALLOWED_TYPES: '*', // Allow all types, or specify: ['image/*', 'application/pdf', 'text/*']
};

// UI Configuration
const UI_CONFIG = {
    TOAST_DURATION: 3000,
    DEBOUNCE_DELAY: 300,
    RECONNECT_INTERVAL: 3000
};
