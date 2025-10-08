.PHONY: help up down logs rebuild test test-coverage format lint typecheck clean

help: ## Показать доступные команды
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Запустить все сервисы (production mode)
	docker compose up -d --build
	@echo "Сервисы запущены (production mode):"
	@echo "  - Board Service: http://localhost:8000"
	@echo "  - File Service: http://localhost:8001"
	@echo "  - Frontend: http://localhost:3000"
	@echo "  - MinIO Console: http://localhost:9001"

up-dev: ## Запустить все сервисы (development mode с hot-reload)
	docker compose -f docker compose.yml -f docker compose.dev.yml up -d --build
	@echo "Сервисы запущены (development mode с hot-reload):"
	@echo "  - Board Service: http://localhost:8000"
	@echo "  - File Service: http://localhost:8001"
	@echo "  - Frontend: http://localhost:3000"
	@echo "  - MinIO Console: http://localhost:9001"

down: ## Остановить все сервисы
	docker compose down

down-volumes: ## Остановить все сервисы и удалить volumes (полная очистка)
	docker compose down -v

logs: ## Показать логи всех сервисов
	docker compose logs -f

logs-board: ## Показать логи board_service
	docker compose logs -f board_service

logs-file: ## Показать логи file_service
	docker compose logs -f file_service

rebuild: ## Пересобрать и перезапустить все контейнеры
	docker compose down
	docker compose up --build -d

test: ## Запустить все тесты
	@echo "Запуск тестов board_service..."
	docker compose run --rm board_service pytest -v
	@echo "\nЗапуск тестов file_service..."
	docker compose run --rm file_service pytest -v

test-board: ## Запустить тесты board_service
	docker compose run --rm board_service pytest -v

test-file: ## Запустить тесты file_service
	docker compose run --rm file_service pytest -v

test-coverage: ## Запустить тесты с покрытием
	@echo "Тесты board_service с покрытием..."
	docker compose run --rm board_service pytest --cov=board_service --cov-report=html --cov-report=term
	@echo "\nТесты file_service с покрытием..."
	docker compose run --rm file_service pytest --cov=file_service --cov-report=html --cov-report=term

format: ## Форматировать код с помощью black
	@echo "Форматирование board_service..."
	docker compose run --rm board_service black .
	@echo "Форматирование file_service..."
	docker compose run --rm file_service black .

lint: ## Проверить код линтером (ruff)
	@echo "Линтинг board_service..."
	docker compose run --rm board_service ruff check .
	@echo "Линтинг file_service..."
	docker compose run --rm file_service ruff check .

typecheck: ## Проверить типы с помощью mypy
	@echo "Проверка типов board_service..."
	docker compose run --rm board_service mypy board_service
	@echo "Проверка типов file_service..."
	docker compose run --rm file_service mypy file_service

clean: ## Удалить все контейнеры, volumes и образы
	docker compose down -v --remove-orphans
	docker system prune -f

db-migrate: ## Создать новую миграцию
	@read -p "Введите описание миграции: " desc; \
	docker compose run --rm board_service alembic revision --autogenerate -m "$$desc"

db-upgrade: ## Применить миграции
	docker compose run --rm board_service alembic upgrade head

db-downgrade: ## Откатить последнюю миграцию
	docker compose run --rm board_service alembic downgrade -1

shell-board: ## Открыть shell в board_service
	docker compose run --rm board_service /bin/bash

shell-file: ## Открыть shell в file_service
	docker compose run --rm file_service /bin/bash

shell-db: ## Открыть psql в PostgreSQL
	docker compose exec postgres psql -U postgres -d board_db

install-dev: ## Установить зависимости для локальной разработки
	cd board_service && pip install -r requirements.txt
	cd file_service && pip install -r requirements.txt

dev-board: ## Запустить board_service локально
	cd board_service && uvicorn main:app --reload --port 8000

dev-file: ## Запустить file_service локально
	cd file_service && uvicorn main:app --reload --port 8001
