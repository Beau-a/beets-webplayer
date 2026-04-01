.PHONY: backend frontend dev lint test

backend:
	cd backend && venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

frontend:
	cd frontend && npm run dev

dev:
	@echo "Start backend and frontend in separate terminals:"
	@echo "  make backend"
	@echo "  make frontend"

lint-backend:
	cd backend && venv/bin/python -m py_compile app/main.py app/config.py app/dependencies.py

test-backend:
	cd backend && venv/bin/python -m pytest tests/ -v

install:
	cd backend && venv/bin/pip install -r requirements.txt
	cd frontend && npm install
