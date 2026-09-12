.PHONY: help build up down logs restart test migrate seed clean

help:
	@echo "Inventory Management System - Make Commands"
	@echo "  build    - Build Docker containers"
	@echo "  up       - Start the stack in background"
	@echo "  down     - Stop and remove containers"
	@echo "  logs     - View API container logs"
	@echo "  restart  - Restart API container"
	@echo "  test     - Run pytest suite inside container"
	@echo "  migrate  - Run Alembic migrations to head"
	@echo "  seed     - Populate database with initial mock/demo data"
	@echo "  clean    - Remove cached files and pyc"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f api

restart:
	docker compose restart api

test:
	docker compose exec api pytest tests/ -v

migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python scripts/seed_data.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
