# ============================================================================
# Makefile for FastAPI Production Project
# ============================================================================

.PHONY: help
help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# Environment Setup
# ============================================================================

.PHONY: install
install: ## Install dependencies using poetry
	poetry install

.PHONY: install-dev
install-dev: ## Install all dependencies including dev
	poetry install --with dev

.PHONY: update
update: ## Update dependencies
	poetry update

.PHONY: lock
lock: ## Lock dependencies
	poetry lock --no-update

.PHONY: env
env: ## Copy .env.example to .env
	cp -n .env.example .env || true

.PHONY: pre-commit-install
pre-commit-install: ## Install pre-commit hooks
	pre-commit install --install-hooks
	pre-commit install --hook-type commit-msg

# ============================================================================
# Docker Commands
# ============================================================================

.PHONY: docker-build
docker-build: ## Build docker images
	docker-compose build

.PHONY: docker-up
docker-up: ## Start docker containers
	docker-compose up -d

.PHONY: docker-down
docker-down: ## Stop docker containers
	docker-compose down

.PHONY: docker-logs
docker-logs: ## Show docker logs
	docker-compose logs -f

.PHONY: docker-clean
docker-clean: ## Remove docker containers and volumes
	docker-compose down -v --remove-orphans

.PHONY: docker-shell
docker-shell: ## Open shell in app container
	docker-compose exec app bash

.PHONY: docker-db-shell
docker-db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres

# ============================================================================
# Database Commands
# ============================================================================

.PHONY: db-upgrade
db-upgrade: ## Apply database migrations
	alembic upgrade head

.PHONY: db-downgrade
db-downgrade: ## Rollback one migration
	alembic downgrade -1

.PHONY: db-migration
db-migration: ## Create new migration
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

.PHONY: db-history
db-history: ## Show migration history
	alembic history

.PHONY: db-current
db-current: ## Show current migration
	alembic current

.PHONY: db-reset
db-reset: ## Reset database (CAUTION: destroys all data)
	alembic downgrade base
	alembic upgrade head

# ============================================================================
# Development Commands
# ============================================================================

.PHONY: run
run: ## Run development server
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: run-prod
run-prod: ## Run production server
	uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4

.PHONY: shell
shell: ## Open IPython shell with app context
	ipython -i scripts/shell.py

.PHONY: routes
routes: ## Show all API routes
	python scripts/show_routes.py

# ============================================================================
# Code Quality Commands
# ============================================================================

.PHONY: format
format: ## Format code using black and ruff
	ruff check --fix .
	ruff format .

.PHONY: lint
lint: ## Run all linters
	ruff check .
	mypy src
	bandit -r src -f json -o bandit-report.json

.PHONY: type-check
type-check: ## Run type checking with mypy
	mypy src --show-error-codes --pretty

.PHONY: security
security: ## Run security checks
	bandit -r src
	pip-audit
	safety check

.PHONY: pre-commit
pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

# ============================================================================
# Testing Commands
# ============================================================================

.PHONY: test
test: ## Run all tests
	pytest

.PHONY: test-unit
test-unit: ## Run unit tests only
	pytest tests/unit -v

.PHONY: test-integration
test-integration: ## Run integration tests only
	pytest tests/integration -v

.PHONY: test-e2e
test-e2e: ## Run end-to-end tests only
	pytest tests/e2e -v

.PHONY: test-cov
test-cov: ## Run tests with coverage
	pytest --cov=src --cov-report=html --cov-report=term-missing

.PHONY: test-watch
test-watch: ## Run tests in watch mode
	ptw -- --lf -vv

.PHONY: coverage
coverage: ## Generate coverage report
	coverage run -m pytest
	coverage html
	@echo "Coverage report generated at htmlcov/index.html"

# ============================================================================
# Documentation Commands
# ============================================================================

.PHONY: docs
docs: ## Generate API documentation
	python scripts/generate_openapi.py > docs/openapi.json

.PHONY: docs-serve
docs-serve: ## Serve documentation locally
	mkdocs serve

.PHONY: docs-build
docs-build: ## Build documentation
	mkdocs build

# ============================================================================
# Cleaning Commands
# ============================================================================

.PHONY: clean
clean: ## Clean build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".DS_Store" -delete 2>/dev/null || true

.PHONY: clean-docker
clean-docker: ## Clean Docker resources
	docker-compose down -v --remove-orphans
	docker system prune -f

.PHONY: clean-all
clean-all: clean clean-docker ## Clean everything

# ============================================================================
# Utility Commands
# ============================================================================

.PHONY: generate-secret
generate-secret: ## Generate secret key for .env
	@python -c "import secrets; print(f'SECRET_KEY={secrets.token_urlsafe(32)}')"

.PHONY: check-env
check-env: ## Validate environment variables
	python scripts/check_env.py

.PHONY: export-requirements
export-requirements: ## Export requirements.txt from poetry
	poetry export -f requirements.txt --output requirements.txt --without-hashes
	poetry export -f requirements.txt --output requirements-dev.txt --with dev --without-hashes

.PHONY: tree
tree: ## Show project structure
	tree -I '__pycache__|*.pyc|.git|.venv|venv|.mypy_cache|.pytest_cache|htmlcov|.ruff_cache' -a

# ============================================================================
# CI/CD Commands
# ============================================================================

.PHONY: ci-lint
ci-lint: ## Run linting for CI
	ruff check --output-format=github .
	mypy src --junit-xml=mypy-report.xml

.PHONY: ci-test
ci-test: ## Run tests for CI
	pytest --junitxml=pytest-report.xml --cov=src --cov-report=xml

.PHONY: ci-security
ci-security: ## Run security checks for CI
	bandit -r src -f json -o bandit-report.json
	safety check --json

# ============================================================================
# Release Commands
# ============================================================================

.PHONY: version
version: ## Show current version
	@poetry version

.PHONY: version-patch
version-patch: ## Bump patch version
	poetry version patch
	git add pyproject.toml
	git commit -m "chore: bump patch version"

.PHONY: version-minor
version-minor: ## Bump minor version
	poetry version minor
	git add pyproject.toml
	git commit -m "chore: bump minor version"

.PHONY: version-major
version-major: ## Bump major version
	poetry version major
	git add pyproject.toml
	git commit -m "chore: bump major version"

# Default target
.DEFAULT_GOAL := help