.PHONY: install lint test check db-up db-down migrate api load-complaints load-embeddings backfill-topics

install:
	pip install -r requirements.txt

lint:
	ruff check src tests scripts

test:
	pytest

check: lint test

db-up:
	docker compose up -d

db-down:
	docker compose down

migrate:
	alembic upgrade head

api:
	uvicorn customer_voice_ai.api.main:app --reload

load-complaints:
	python -m customer_voice_ai.data.load_complaints_to_db

load-embeddings:
	python -m customer_voice_ai.data.load_embeddings_to_db

backfill-topics:
	python scripts/backfill_topic_embeddings.py