# 🗂️ Kanban Board - Microservices Architecture

Production-ready канбан-доска с микросервисной архитектурой, реализованная на FastAPI с использованием принципов Clean Architecture и SOLID.

## 📋 Оглавление

- [Архитектура](#архитектура)
- [Технологический стек](#технологический-стек)
- [Структура проекта](#структура-проекта)
- [Быстрый старт](#быстрый-старт)
- [API документация](#api-документация)
- [Тестирование](#тестирование)
- [Разработка](#разработка)

## 🏗️ Архитектура

### Микросервисы

Проект состоит из двух независимых микросервисов:

#### 1. **board_service** (порт 8000)
- Управление канбан-доской и задачами
- CRUD операции для задач
- Перемещение задач между колонками (To Do → In Progress → Done)
- WebSocket для real-time обновлений
- REST API для взаимодействия

#### 2. **file_service** (порт 8001)
- Загрузка и хранение файлов в S3 (MinIO)
- Управление вложениями задач
- Генерация presigned URLs для безопасного доступа
- REST API для файловых операций



## 🛠️ Технологический стек

| Компонент          | Технология            |
|--------------------|-----------------------|
| Язык               | Python 3.12+          |
| Web Framework      | FastAPI               |
| ORM                | SQLAlchemy (async)    |
| База данных        | PostgreSQL            |
| Хранилище файлов   | MinIO (S3-compatible) |
| Миграции           | Alembic               |
| Тестирование       | pytest, pytest-asyncio|
| Линтинг            | ruff, mypy            |
| Форматирование     | black                 |
| Контейнеризация    | Docker, Docker Compose|
| WebSocket          | FastAPI WebSocket     |

## 📁 Структура проекта

```
kanban/
├── board_service/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py              # Dependency injection
│   │   ├── tasks.py             # Task endpoints
│   │   └── websocket.py         # WebSocket connections
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Конфигурация
│   │   └── database.py          # Database setup
│   ├── models/
│   │   ├── __init__.py
│   │   └── task.py              # SQLAlchemy models
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── task_repository.py   # Data access layer
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── task.py              # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── task_service.py      # Business logic
│   │   └── websocket_manager.py # WebSocket manager
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_tasks.py
│   │   └── test_websocket.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
│
├── file_service/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── files.py             # File endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── s3.py                # S3/MinIO client
│   ├── models/
│   │   ├── __init__.py
│   │   └── file.py              # File metadata model
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── file_repository.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── file.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_service.py
│   │   └── s3_service.py        # S3 operations
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   └── test_files.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
│
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose

### Установка и запуск

1. **Клонировать репозиторий и перейти в директорию:**

```bash
cd kanban
```

2. **Создать файл окружения:**

```bash
cp .env.example .env
```

3. **Запустить все сервисы:**

```bash
docker compose up -d --build

```

Сервисы будут доступны по адресам:
- Web: http://localhost:3000
- Board Service: http://localhost:8000
- File Service: http://localhost:8001
- MinIO Console: http://localhost:9001 (admin/adminpassword)
- PostgreSQL: localhost:5432

## 📚 API документация

### Board Service API

Swagger UI доступен по адресу: http://localhost:8000/docs

#### Основные endpoints:

**Задачи:**
- `POST /api/v1/tasks` - Создать задачу
- `GET /api/v1/tasks` - Получить все задачи
- `GET /api/v1/tasks/{task_id}` - Получить задачу по ID
- `PUT /api/v1/tasks/{task_id}` - Обновить задачу
- `PATCH /api/v1/tasks/{task_id}/status` - Изменить статус задачи
- `DELETE /api/v1/tasks/{task_id}` - Удалить задачу

**WebSocket:**
- `WS /ws` - WebSocket подключение для real-time обновлений

### File Service API

Swagger UI доступен по адресу: http://localhost:8001/docs

#### Основные endpoints:

**Файлы:**
- `POST /api/v1/files/upload` - Загрузить файл
- `GET /api/v1/files/{file_id}` - Получить метаданные файла
- `GET /api/v1/files/{file_id}/download` - Скачать файл
- `DELETE /api/v1/files/{file_id}` - Удалить файл
- `GET /api/v1/files/task/{task_id}` - Получить все файлы задачи

## 🧪 Тестирование

### Запуск всех тестов

```bash
docker compose run --rm board_service pytest
```
```bash
docker compose run --rm file_service pytest
```


### Запуск конкретного теста

```bash
# Board service
docker-compose run --rm board_service pytest tests/test_tasks.py::test_create_task

# File service
docker-compose run --rm file_service pytest tests/test_files.py::test_upload_file
```


### Миграции базы данных

```bash
# Создать новую миграцию
docker-compose run --rm board_service alembic revision --autogenerate -m "description"
docker-compose run --rm file_service alembic revision --autogenerate -m "description"
# Применить миграции
docker-compose run --rm board_service alembic upgrade head
docker-compose run --rm file_service alembic upgrade head

# Откатить миграцию
docker-compose run --rm board_service alembic downgrade -1
```

## 🔧 Конфигурация

Все настройки конфигурируются через переменные окружения в файле `.env`:

```env
# Board Service
BOARD_DB_HOST=postgres
BOARD_DB_PORT=5432
BOARD_DB_NAME=board_db
BOARD_DB_USER=postgres
BOARD_DB_PASSWORD=postgres

# File Service
FILE_DB_HOST=postgres
FILE_DB_PORT=5432
FILE_DB_NAME=file_db
FILE_DB_USER=postgres
FILE_DB_PASSWORD=postgres

# MinIO (S3)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_NAME=kanban-files

# Services
FILE_SERVICE_URL=http://file_service:8001
```

## 📖 Дополнительная информация

### Статусы задач

Задачи могут находиться в одном из трех статусов:
- `todo` - To Do (задача создана, не начата)
- `in_progress` - In Progress (задача в работе)
- `done` - Done (задача завершена)

### WebSocket события

При изменении задач через API, все подключенные клиенты получают события:
- `task_created` - Создана новая задача
- `task_updated` - Задача обновлена
- `task_deleted` - Задача удалена
- `task_status_changed` - Изменен статус задачи

### Безопасность

- Все S3 URLs являются presigned и имеют ограниченное время жизни
- Валидация входных данных через Pydantic
- Ограничение размера загружаемых файлов (настраивается)
- CORS настроен для безопасного взаимодействия с фронтендом
