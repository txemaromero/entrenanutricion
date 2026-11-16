COMPOSE ?= docker compose

.PHONY: up down build logs migrate seed test test-backend test-frontend lint e2e

up:            ## Start db, backend and frontend (http://localhost:5173)
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs -f

migrate:
	$(COMPOSE) exec backend python manage.py migrate

seed:          ## Load idempotent demo data
	$(COMPOSE) exec backend python manage.py seed_demo

test: test-backend test-frontend

test-backend:
	$(COMPOSE) exec backend pytest --cov

test-frontend:
	$(COMPOSE) exec frontend npm test

lint:
	$(COMPOSE) exec backend ruff check .
	$(COMPOSE) exec backend black --check .
	$(COMPOSE) exec frontend npm run lint

e2e:           ## Playwright against the running stack (seeded)
	cd frontend && npx playwright test
