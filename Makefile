.PHONY: help install install-dev build up down restart logs clean test test-unit test-api seed lint format check-types

help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install      - Install dependencies from pyproject.toml"
	@echo "  make install-dev  - Install dev dependencies"
	@echo "  make format       - Format code with black"
	@echo "  make lint         - Lint code with ruff"
	@echo "  make check-types  - Check types with mypy"
	@echo ""
	@echo "Docker:"
	@echo "  make build        - Build Docker images"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make restart      - Restart all services"
	@echo "  make logs         - View application logs"
	@echo "  make clean        - Remove all containers and volumes"
	@echo ""
	@echo "Testing:"
	@echo "  make test         - Run all tests (unit + API integration)"
	@echo "  make test-unit    - Run pytest unit tests"
	@echo "  make test-api     - Run bash API integration tests (requires services)"
	@echo "  make seed         - Re-seed the database"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

format:
	black app/ scripts/ alembic/

lint:
	ruff check app/ scripts/ alembic/

check-types:
	mypy app/ scripts/

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services started!"
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f app

clean:
	docker-compose down -v
	@echo "All containers and volumes removed"

test: test-unit test-api
	@echo "All tests completed!"

test-unit:
	@echo "Running pytest unit tests..."
	pytest

test-api:
	@echo "Running API integration tests..."
	@bash test_api.sh

seed:
	docker-compose exec app python scripts/seed_data.py
