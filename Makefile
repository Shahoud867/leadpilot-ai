.PHONY: setup migrate seed api web test build demo
setup:
	python -m venv .venv
	.venv/bin/pip install -r services/api/requirements.txt
	cd apps/web && npm ci
migrate:
	.venv/bin/python -m alembic -c services/api/alembic.ini upgrade head
seed:
	.venv/bin/python scripts/seed.py --seed 20261108 --reset --scenario all
api:
	.venv/bin/uvicorn app.main:app --app-dir services/api --host 127.0.0.1 --port 8000
web:
	cd apps/web && npm run dev
build:
	cd apps/web && npm run build
test:
	.venv/bin/pytest services/api/tests -q
	cd apps/web && npm test
demo:
	.venv/bin/python scripts/run_demo.py
