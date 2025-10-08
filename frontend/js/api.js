// API Service
class ApiService {
    constructor() {
        this.boardServiceUrl = API_CONFIG.BOARD_SERVICE;
        this.fileServiceUrl = API_CONFIG.FILE_SERVICE;
    }

    // Generic request handler
    async request(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    // ===== Task API =====
    
    async getTasks(status = null) {
        const url = status 
            ? `${this.boardServiceUrl}${ENDPOINTS.TASKS.LIST}?status=${status}`
            : `${this.boardServiceUrl}${ENDPOINTS.TASKS.LIST}`;
        return this.request(url);
    }

    async getTask(id) {
        const url = `${this.boardServiceUrl}${ENDPOINTS.TASKS.GET(id)}`;
        return this.request(url);
    }

    async createTask(taskData) {
        const url = `${this.boardServiceUrl}${ENDPOINTS.TASKS.CREATE}`;
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(taskData)
        });
    }

    async updateTask(id, taskData) {
        const url = `${this.boardServiceUrl}${ENDPOINTS.TASKS.UPDATE(id)}`;
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(taskData)
        });
    }

    async updateTaskStatus(id, status) {
        const url = `${this.boardServiceUrl}${ENDPOINTS.TASKS.UPDATE_STATUS(id)}`;
        return this.request(url, {
            method: 'PATCH',
            body: JSON.stringify({ status })
        });
    }

    async deleteTask(id) {
        const url = `${this.boardServiceUrl}${ENDPOINTS.TASKS.DELETE(id)}`;
        return this.request(url, { method: 'DELETE' });
    }

    // ===== File API =====
    
    async uploadFile(file, taskId, uploadedBy = 'user') {
        try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('task_id', taskId);
            formData.append('uploaded_by', uploadedBy);

            const url = `${this.fileServiceUrl}${ENDPOINTS.FILES.UPLOAD}`;
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Upload failed: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('File upload failed:', error);
            throw error;
        }
    }

    async getFilesByTask(taskId) {
        const url = `${this.fileServiceUrl}${ENDPOINTS.FILES.BY_TASK(taskId)}`;
        return this.request(url);
    }

    async getFile(id) {
        const url = `${this.fileServiceUrl}${ENDPOINTS.FILES.GET(id)}`;
        return this.request(url);
    }

    async downloadFile(id) {
        try {
            const url = `${this.fileServiceUrl}${ENDPOINTS.FILES.DOWNLOAD(id)}`;
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Download failed: ${response.status}`);
            }

            const blob = await response.blob();
            const contentDisposition = response.headers.get('content-disposition');
            const filename = contentDisposition
                ? contentDisposition.split('filename=')[1].replace(/"/g, '')
                : 'download';

            // Create download link
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(downloadUrl);

            return true;
        } catch (error) {
            console.error('File download failed:', error);
            throw error;
        }
    }

    async deleteFile(id) {
        const url = `${this.fileServiceUrl}${ENDPOINTS.FILES.DELETE(id)}`;
        return this.request(url, { method: 'DELETE' });
    }
}

// Export singleton instance
const api = new ApiService();
