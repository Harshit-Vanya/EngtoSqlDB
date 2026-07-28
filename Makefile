.PHONY: help install dev test lint format run docker-up docker-down migrate seed

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -e .

dev: ## Install development dependencies
	pip install -e ".[dev,data]"

test: ## Run tests
	pytest tests/ -v --cov=backend/app --cov-report=term-missing

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests
	pytest tests/e2e/ -v

lint: ## Run linter
	ruff check backend/ tests/ data_pipeline/ evaluation/
	mypy backend/app/

format: ## Format code
	ruff format backend/ tests/ data_pipeline/ evaluation/
	ruff check --fix backend/ tests/ data_pipeline/ evaluation/

run: ## Run the backend server locally
	uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

docker-up: ## Start all services with Docker
	docker compose -f docker/docker-compose.yml up --build -d

docker-down: ## Stop all Docker services
	docker compose -f docker/docker-compose.yml down

docker-logs: ## Tail Docker logs
	docker compose -f docker/docker-compose.yml logs -f

migrate: ## Run database migrations
	cd backend && alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	cd backend && alembic revision --autogenerate -m "$(MSG)"

seed: ## Seed the database with sample data
	python -m data_pipeline.seeds.seed_database

index-schema: ## Index schema metadata into vector store
	python -m data_pipeline.schema_catalog.indexer

evaluate: ## Run evaluation benchmark
	python -m evaluation.runner

clean: ## Remove generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage
