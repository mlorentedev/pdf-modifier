# =============================================================================
# Makefile — PDF Modifier
# =============================================================================

SHELL := /bin/bash
.SHELLFLAGS := -c -o pipefail

UV := uv
APP_NAME := pdf-modifier
COMPOSE := docker compose
COMPOSE_FILES := -f infra/compose.base.yml -f infra/compose.dev.yml
COMPOSE_PROD := -f infra/compose.base.yml -f infra/compose.prod.yml
ENV_FILE := infra/.env
ENV_EXAMPLE := .env.example

# Default target for commands with TARGET argument
TARGET ?= all

.DEFAULT_GOAL := help

# =============================================================================
# Help
# =============================================================================
.PHONY: help
help: ## Show available targets
	@echo "=== PDF Modifier ==="
	@echo ""
	@echo "Setup:"
	@echo "  make setup                  Install all deps"
	@echo "  make setup backend          Install backend deps only"
	@echo "  make setup frontend         Install frontend deps only"
	@echo "  make env                    Generate $(ENV_FILE) from example (idempotent)"
	@echo ""
	@echo "Run:"
	@echo "  make run api                Start FastAPI dev server"
	@echo "  make run mcp                Start MCP server"
	@echo "  make run cli ARGS=          Run CLI"
	@echo "  make run frontend           Start frontend dev server"
	@echo ""
	@echo "Test:"
	@echo "  make test                   Run all tests"
	@echo "  make test backend           Run backend tests only"
	@echo "  make test frontend          Run frontend tests only"
	@echo ""
	@echo "Quality:"
	@echo "  make check                  Lint + type + test (backend)"
	@echo "  make check-frontend         svelte-check + vitest (frontend)"
	@echo "  make test-e2e               Playwright e2e (starts stack)"
	@echo "  make lint                   Ruff check"
	@echo "  make format                 Ruff fix"
	@echo "  make type                   Mypy"
	@echo "  make mutation               Mutmut mutation testing"
	@echo ""
	@echo "Docker:"
	@echo "  make up                     Start dev stack"
	@echo "  make down                   Stop dev stack"
	@echo "  make logs                   Follow logs"
	@echo "  make ps                     List services"
	@echo "  make status                 Start + verify health"
	@echo "  make up prod                Start production stack"
	@echo "  make down prod              Stop production stack"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean                  Remove build artifacts"
	@echo "  make housekeep              Clean Python + Docker"

# =============================================================================
# Env
# =============================================================================
.PHONY: env
env: ## Generate $(ENV_FILE) from $(ENV_EXAMPLE) (idempotent; FORCE=1 to regenerate)
	@mkdir -p infra
	@python3 scripts/gen-env.py $(if $(filter 1,$(FORCE)),--force,)

# =============================================================================
# Setup
# =============================================================================
.PHONY: setup
setup: ## Install deps (TARGET: all|backend|frontend)
ifeq ($(TARGET),frontend)
	cd frontend && npm install
	$(MAKE) --no-print-directory pdf-worker
	@echo "[OK] Frontend ready"
else ifeq ($(TARGET),backend)
	cd backend && $(UV) sync --all-extras
	@echo "[OK] Backend ready"
else
	cd backend && $(UV) sync --all-extras
	cd frontend && npm install
	$(MAKE) --no-print-directory pdf-worker
	@echo "[OK] All deps ready"
endif

# pdf.js loads its worker from /pdf.worker.min.mjs (PdfPreview.svelte). The file
# is gitignored and must match the installed pdfjs-dist, so it is re-copied from
# node_modules on every setup and dev run. The Docker image copies it at build.
.PHONY: pdf-worker
pdf-worker:
	cp frontend/node_modules/pdfjs-dist/build/pdf.worker.min.mjs frontend/static/

# =============================================================================
# Run
# =============================================================================
.PHONY: run
run: ## Run service (TARGET: api|mcp|cli|frontend)
ifeq ($(TARGET),api)
	cd backend && $(UV) run uvicorn pdf_modifier.web.app:create_app --factory --reload --host 0.0.0.0 --port 8000
else ifeq ($(TARGET),mcp)
	cd backend && $(UV) run pdf-modifier
else ifeq ($(TARGET),cli)
	cd backend && $(UV) run pdf-mod $(ARGS)
else ifeq ($(TARGET),frontend)
	$(MAKE) --no-print-directory pdf-worker
	cd frontend && npm run dev
else
	@echo "Usage: make run TARGET=api|mcp|cli|frontend"
endif

# =============================================================================
# Test
# =============================================================================
.PHONY: test
test: ## Run tests (TARGET: all|backend|frontend)
ifeq ($(TARGET),backend)
	cd backend && $(UV) run pytest --cov=src --cov-report=term-missing --cov-report=xml
else ifeq ($(TARGET),frontend)
	cd frontend && npm test
else
	cd backend && $(UV) run pytest --cov=src --cov-report=term-missing --cov-report=xml
	cd frontend && npm test
endif

# =============================================================================
# Quality (Backend)
# =============================================================================
.PHONY: check
check: lint type test-backend ## Lint + type + test

.PHONY: check-frontend
check-frontend: ## svelte-check + vitest (frontend)
	cd frontend && npm run check
	cd frontend && npm test

.PHONY: test-e2e
test-e2e: up ## Playwright e2e against the running Docker stack
	cd frontend && npm run test:e2e

.PHONY: lint
lint: ## Ruff check
	cd backend && $(UV) run ruff check src/ tests/

.PHONY: format
format: ## Ruff fix
	cd backend && $(UV) run ruff format src/ tests/
	cd backend && $(UV) run ruff check --fix src/ tests/

.PHONY: type
type: ## Mypy
	cd backend && $(UV) run mypy src/

.PHONY: test-backend
test-backend: ## Backend tests only
	cd backend && $(UV) run pytest --cov=src --cov-report=term-missing --cov-report=xml

.PHONY: test-unit
test-unit: ## Unit tests only
	cd backend && $(UV) run pytest tests/unit/ -v

.PHONY: test-int
test-int: ## Integration tests only
	cd backend && $(UV) run pytest tests/integration/ -v

.PHONY: mutation
mutation: ## Mutmut mutation testing
	cd backend && $(UV) run mutmut run
	cd backend && $(UV) run mutmut results

.PHONY: build-frontend
build-frontend: ## Build frontend for production
	cd frontend && npm run build

# =============================================================================
# Docker
# =============================================================================
.PHONY: up
up: env ## Start dev stack (or TARGET=prod)
ifeq ($(TARGET),prod)
	$(COMPOSE) $(COMPOSE_PROD) up -d --build
else
	$(COMPOSE) $(COMPOSE_FILES) up -d --build
	@echo "API: http://localhost:8000 | Web: http://localhost:8080"
endif

.PHONY: down
down: ## Stop dev stack (or TARGET=prod)
ifeq ($(TARGET),prod)
	$(COMPOSE) $(COMPOSE_PROD) down
else
	$(COMPOSE) $(COMPOSE_FILES) down --remove-orphans
endif

.PHONY: logs
logs: ## Follow logs (or TARGET=prod)
ifeq ($(TARGET),prod)
	$(COMPOSE) $(COMPOSE_PROD) logs -f --tail=100
else
	$(COMPOSE) $(COMPOSE_FILES) logs -f --tail=100
endif

.PHONY: ps
ps: ## List services (or TARGET=prod)
ifeq ($(TARGET),prod)
	$(COMPOSE) $(COMPOSE_PROD) ps
else
	$(COMPOSE) $(COMPOSE_FILES) ps
endif

.PHONY: status
status: up ## Start + verify health
	@sleep 5
	@curl -sf http://localhost:8000/health && echo " [OK] API" || echo " [FAIL] API"
	@curl -sf http://localhost:8080/health && echo " [OK] Web" || echo " [FAIL] Web"

# =============================================================================
# Cleanup
# =============================================================================
.PHONY: clean
clean: ## Remove build artifacts
	cd backend && rm -rf dist/ build/ *.egg-info .coverage coverage.xml htmlcov/
	cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "[OK] Cleaned"

.PHONY: docker-clean
docker-clean: ## Remove Docker images + containers
	@docker rmi $(APP_NAME)-api:latest $(APP_NAME)-web:latest 2>/dev/null || true
	@docker rm -f test-pdf-mod 2>/dev/null || true
	@echo "[OK] Docker cleaned"

.PHONY: housekeep
housekeep: ## Clean Python + Docker
	cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	cd backend && find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	cd backend && rm -rf dist/ build/ *.egg-info .coverage coverage.xml htmlcov/
	@docker container prune -f 2>/dev/null || true
	@docker image prune -f 2>/dev/null || true
	@echo "[OK] Housekeeping done"
