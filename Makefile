.PHONY: install lint test check db-up db-down migrate api load-complaints load-embeddings backfill-topics backfill-csi eval-rag train-embedding-classifier ingest-cfpb-api ingest-cfpb-csv

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

backfill-csi:
	python scripts/backfill_csi_fields.py

eval-rag:
	python -m customer_voice_ai.evaluation.evaluate_rag_retrieval

train-embedding-classifier:
	python -m customer_voice_ai.ml.train_product_embedding_classifier

ingest-cfpb-api:
	python -m customer_voice_ai.data.ingest_cfpb --source api --rows 20000 --fallback-csv-path data/raw/complaints.csv

ingest-cfpb-csv:
	python -m customer_voice_ai.data.ingest_cfpb --source csv --csv-path data/raw/complaints.csv --rows 20000