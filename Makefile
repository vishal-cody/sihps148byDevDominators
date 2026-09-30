.PHONY: install dev test lint build clean seed docker-up docker-down

# ─────────────────────────────────────────────
# JOCKY Platform — Developer Makefile
# ─────────────────────────────────────────────

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Installing compiler dependencies..."
	cd compiler && pip install -r requirements.txt 2>/dev/null || true
	@echo "✓ All dependencies installed"

dev:
	@echo "Starting JOCKY development servers..."
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:5173"
	@echo "  API Docs: http://localhost:8000/docs"
	@start cmd /k "cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
	@cd frontend && npm run dev

seed:
	@echo "Seeding demo data..."
	cd backend && python -m app.db.seed
	@echo "✓ Demo data seeded"

test:
	@echo "Running compiler tests..."
	cd compiler && python -m pytest tests/ -v
	@echo "Running backend tests..."
	cd backend && python -m pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && npm test -- --run
	@echo "✓ All tests complete"

test-compiler:
	cd compiler && python -m pytest tests/ -v --tb=short

test-backend:
	cd backend && python -m pytest tests/ -v --tb=short

test-frontend:
	cd frontend && npm test -- --run

lint:
	@echo "Linting backend..."
	cd backend && ruff check . && mypy app/ --ignore-missing-imports
	@echo "Linting compiler..."
	cd compiler && ruff check .
	@echo "Linting frontend..."
	cd frontend && npm run lint

build:
	@echo "Building frontend production bundle..."
	cd frontend && npm run build
	@echo "✓ Build complete: frontend/dist/"

docker-up:
	docker compose up --build -d
	@echo "✓ JOCKY Platform started"
	@echo "  Frontend: http://localhost:5173"
	@echo "  Backend:  http://localhost:8000"
	@echo "  API Docs: http://localhost:8000/docs"

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf frontend/dist frontend/node_modules/.cache
	rm -rf backend/jocky_dev.db
	@echo "✓ Cleaned"

migrate:
	cd backend && alembic upgrade head

migrate-new:
	cd backend && alembic revision --autogenerate -m "$(MSG)"

demo:
	@echo "Opening JOCKY demo..."
	@echo "Admin credentials: admin / admin123"
	@start http://localhost:5173
