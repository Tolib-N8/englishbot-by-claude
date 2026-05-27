.PHONY: help install backend-install frontend-install dev backend-dev frontend-dev migrate revision test fmt clean

help:
	@echo "English Learning App"
	@echo ""
	@echo "Setup (run once):"
	@echo "  make install            install backend (venv) + frontend (npm)"
	@echo ""
	@echo "Development:"
	@echo "  make backend-dev        run FastAPI at :8000 (uses your Claude Code login)"
	@echo "  make frontend-dev       run Next.js at :3000"
	@echo "  make dev                start both (needs tmux/screen if you want one terminal)"
	@echo ""
	@echo "DB:"
	@echo "  make migrate            apply Alembic migrations"
	@echo "  make revision msg=...   create a new migration"
	@echo ""
	@echo "Quality:"
	@echo "  make test               pytest backend"
	@echo "  make fmt                ruff format backend"

install: backend-install frontend-install

backend-install:
	cd backend && python -m venv .venv && \
		.venv/bin/pip install --upgrade pip && \
		.venv/bin/pip install -e ".[dev]"

frontend-install:
	cd frontend && npm install --legacy-peer-deps

backend-dev:
	cd backend && .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend-dev:
	cd frontend && npm run dev

dev:
	@echo "Open two terminals and run:"
	@echo "  make backend-dev"
	@echo "  make frontend-dev"
	@echo "Or use tmux/screen/your-favorite-runner."

migrate:
	cd backend && .venv/bin/alembic upgrade head

revision:
	@if [ -z "$(msg)" ]; then echo "usage: make revision msg=\"my change\""; exit 1; fi
	cd backend && .venv/bin/alembic revision --autogenerate -m "$(msg)"

test:
	cd backend && .venv/bin/pytest -q

fmt:
	cd backend && .venv/bin/ruff format app tests && .venv/bin/ruff check --fix app tests

clean:
	rm -rf backend/.venv backend/.pytest_cache frontend/node_modules frontend/.next
