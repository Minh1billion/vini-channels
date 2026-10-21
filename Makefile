.PHONY: backend-vapid backend-migrate backend-scheduler backend-api backend-check backend-test frontend-dev frontend-build up down logs docker-check docker-prod docker-prod-down docker-clean

backend-vapid:
	cd backend && PYTHONPATH=src python3 -m vinichannels.adapters.outbound.push.keygen

backend-migrate:
	cd backend && PYTHONPATH=src alembic upgrade head

backend-scheduler:
	cd backend && PYTHONPATH=src python3 -m vinichannels.scheduler_main

backend-api:
	cd backend && PYTHONPATH=src uvicorn vinichannels.main:app --reload --port 8000

backend-test:
	cd backend && python3 -m pytest

backend-check:
	cd backend && ruff check . && mypy && PYTHONPATH=src lint-imports && python3 -m pytest

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f frontend

docker-check:
	docker compose --profile check run --rm --build backend

docker-prod:
	docker compose --profile prod up --build -d web

docker-prod-down:
	docker compose --profile prod stop web

docker-clean:
	docker compose --profile check --profile prod down -v --rmi local
