Ниже описание **только по фактам из репозитория**: коду, README, структуре, зависимостям, миграциям, тестам, Makefile и локальным артефактам. Где точных данных нет, я так и пишу.

# 1. Что это за проект

- **Название проекта:** `Customer Voice AI`
- **Для какого бизнеса создан:** аналитика клиентской обратной связи / “Voice of Customer” / продуктовая аналитика по обращениям и жалобам клиентов.
- **Какую проблему решает:** превращает неструктурированные тексты клиентских жалоб в классификацию продукта, динамические темы, поиск похожих обращений, агрегированную аналитику и ответы AI-агента.
- **Кто пользователи:** продуктовые специалисты, аналитики Customer Voice / CSI, сотрудники, которые разбирают клиентскую обратную связь.
- **Основные сценарии:**
  - классифицировать клиентский комментарий по продуктовой категории;
  - определить, уверена ли модель в классификации;
  - отправить низкоуверенные кейсы на human review;
  - создать новую динамическую тему из reviewed-кейса;
  - найти похожие исторические жалобы через semantic search;
  - получить аналитический ответ агента по запросу;
  - сохранить feedback на ответ агента;
  - посмотреть runtime-метрики классификаций;
  - получить агрегированную аналитику по CSI-like полям.

# 2. Моя роль

Реализовал end-to-end ML/LLM/FastAPI сервис: ETL, ML baseline, RAG, БД, API, миграции, Docker Compose, CI, тесты и документацию.
Проект содержит код приложения, миграции, тесты, CI, Makefile, README и артефакты моделей.

Объективно можно описывать роль как:
- разработка backend/API на FastAPI;
- проектирование PostgreSQL/pgvector схемы;
- разработка ETL для CFPB данных;
- обучение и оценка NLP-классификаторов;
- реализация RAG/semantic search;
- реализация LangGraph agent workflow;
- настройка Docker Compose, Alembic, GitHub Actions, pytest/ruff.

# 3. Архитектура

Основные компоненты:
- FastAPI API service;
- ML classifier: TF-IDF + Logistic Regression;
- embedding service на `sentence-transformers/all-MiniLM-L6-v2`;
- PostgreSQL + pgvector;
- LangGraph agent;
- LLM answer composer через OpenAI-compatible Chat API;
- ETL scripts;
- Alembic migrations;
- CI pipeline.

Модули:
- `api/` — FastAPI routes, schemas, app;
- `data/` — ingestion, CSV/API обработка, загрузка в БД;
- `db/` — SQLAlchemy models, sessions, repositories;
- `ml/` — классификаторы, embeddings, topic matching;
- `rag/` — local vector index и pgvector search;
- `agent/` — LangGraph agent, LLM answer composer, summarizer;
- `evaluation/` — threshold evaluation, RAG retrieval evaluation;
- `scripts/` — backfill CSI fields, topic embeddings, запуск агента.

Схема потоков данных:
0. Client source adapters (deleted) → canonical CSV.
1. CFPB API или CSV → canonical CSV.
2. Canonical CSV → processed classification dataset.
3. Processed dataset → обучение модели продукта.
4. Processed dataset → embeddings → pgvector.
5. FastAPI получает текст → классификатор → статус `known/uncertain`.
6. Если uncertain → запись в `uncertain_classifications`.
7. Если включен topic matching → поиск ближайших тем через pgvector.
8. Все классификации → запись в `classification_events`.
9. Agent endpoint → classification + semantic search + analytics + LLM/fallback answer.
10. Feedback endpoint → запись в `agent_feedback`.

# 4. Источники данных

CFPB Socrata API:
- **Тип:** внешний HTTP API.
- **Формат:** JSON.
- **Откуда:** `https://data.consumerfinance.gov/resource/s6ew-h6mp.json`.
- **Как используется:** загрузка жалоб CFPB с полями complaint id, дата, продукт, issue, компания, штат, текст жалобы и т.д.

CSV:
- **Тип:** локальный файл.
- **Формат:** CSV.
- **Файл:** `data/raw/complaints.csv`, локально размер около 8.1 GB.
- **Как используется:** fallback или основной источник, если API недоступен; читается чанками.

Processed CSV:
- `data/interim/cfpb_complaints_sample.csv` — canonical sample, около 27 MB.
- `data/processed/product_classification_dataset.csv` — датасет классификации, около 7.8 MB.

PostgreSQL:
- **Тип:** relational database.
- **Используется для:** хранения жалоб, embeddings, тем, событий классификации, feedback.

LLM API:
- **Тип:** OpenAI-compatible Chat API.
- **Используется для:** генерации аналитических ответов и summary.
- В `.env.example` и config указаны `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`; дефолтный base URL в коде — `https://api.deepseek.com`.

Не найдено в коде:
- ClickHouse;
- Oracle;
- Google Sheets;
- 1С;
- CRM;
- FTP;
- Email;
- Telegram;
- XML.

# 5. Базы данных

PostgreSQL `customer_voice_ai`:
- поднимается через Docker Compose на образе `pgvector/pgvector:pg16`;
- локальный порт: `55432:5432`;
- используется SQLAlchemy + Alembic.

Основные таблицы:
- `complaints` — жалобы, продукт, issue, company, state, narrative, CSI-like поля, embedding;
- `topics` — динамические темы, source/status/description, embedding;
- `uncertain_classifications` — низкоуверенные классификации для review;
- `classification_events` — runtime events классификации, включая JSONB top predictions/topic matches;
- `agent_feedback` — feedback пользователей на ответы агента.

Примерные объемы по фактам из локальных запусков:
- processed classification dataset: 6,121 строк;
- complaint embeddings artifact: 3,000 embeddings;
- raw CSV: около 8.1 GB;
- vector artifact: `complaint_embeddings.npy` около 4.4 MB.

# 6. SQL

Используются:
- `SELECT`;
- `GROUP BY`;
- `ORDER BY`;
- `LIMIT`;
- `COUNT`;
- `AVG`;
- `HAVING`;
- `WHERE`;
- `INSERT ... ON CONFLICT DO NOTHING`;
- `UPDATE`;
- `CREATE INDEX`;
- `CREATE EXTENSION IF NOT EXISTS vector`.

Агрегации:
- counts by product;
- counts by issue/product;
- monthly counts через `date_trunc` и `to_char`;
- average CSI score;
- runtime counts by classification status, recommended action, topic match status.

JOIN:
- в просмотренном коде JOIN не найден.

CTE:
- не найдено.

Оконные функции:
- не найдено.

Подзапросы:
- явно сложных SQL-подзапросов не видно; в основном SQLAlchemy query builder.

Оптимизация:
- индексы по product, issue, company, status, created_at, score-related fields;
- HNSW индекс pgvector:
  - `ix_complaints_embedding_hnsw`
  - `USING hnsw (embedding vector_cosine_ops)`
  - `WHERE embedding IS NOT NULL`.


# 7. Python

Основные задачи Python:
- ingest данных из API/CSV;
- очистка и canonicalization данных;
- подготовка датасета классификации;
- обучение ML-моделей;
- генерация embeddings;
- загрузка данных и embeddings в PostgreSQL;
- FastAPI backend;
- RAG/semantic search;
- LangGraph agent workflow;
- LLM answer generation;
- аналитические агрегаты;
- тесты и evaluation scripts.

Библиотеки:
- `pandas` — чтение CSV, chunk processing, подготовка датасетов;
- `numpy` — хранение/загрузка embeddings `.npy`;
- `scikit-learn` — TF-IDF, LogisticRegression, train/test split, F1, classification report;
- `sentence-transformers` — embeddings текстов и тем;
- `torch`, `transformers` — зависимости для transformer/embedding стека;
- `joblib` — сохранение моделей и metadata;
- `FastAPI` — REST API;
- `Pydantic` — request/response schemas и settings;
- `SQLAlchemy` — ORM и SQL queries;
- `Alembic` — миграции БД;
- `psycopg` — PostgreSQL driver;
- `pgvector` — vector columns/search в PostgreSQL;
- `requests` — CFPB API ingestion;
- `LangGraph` — agent workflow graph;
- `langchain-openai` — ChatOpenAI-compatible LLM client;
- `pytest` — тесты;
- `ruff` — linting;
- `Docker Compose` — локальная PostgreSQL/pgvector инфраструктура.

# 8. Автоматизация

Автоматизировано:
- загрузка CFPB данных из API;
- fallback на CSV при ошибке API;
- чтение большого CSV чанками;
- canonical schema preparation;
- подготовка balanced classification dataset;
- обучение TF-IDF classifier;
- обучение embedding classifier;
- расчет ML metrics;
- построение embeddings;
- загрузка complaints в PostgreSQL;
- загрузка embeddings в PostgreSQL;
- backfill topic embeddings;
- backfill synthetic CSI-like fields;
- Alembic migrations;
- запуск API;
- lint/test через Makefile;
- CI через GitHub Actions;
- RAG retrieval evaluation.

Проект автоматизирует pipeline от загрузки данных до API/аналитики.

# 9. Аналитика

Показатели:
- total rows;
- top products by count;
- top issues by product;
- monthly product counts;
- average CSI score;
- sentiment counts;
- severity counts;
- lowest CSI products;
- monthly CSI;
- CSI drivers: issue/product pairs с низким avg CSI и минимальным count;
- runtime classification status counts;
- recommended action counts;
- topic match status counts;
- ML macro F1 / weighted F1;
- RAG product hit@5 / issue hit@5.

KPI:
- `macro_f1`;
- `weighted_f1`;
- threshold coverage / uncertain rate / known accuracy / known macro F1 в threshold evaluation;
- retrieval hit@k.

Дашборды:
- Есть API endpoints, которые могут питать dashboard.

# 10. Бизнес-логика

Классификация:
- входной текст проверяется на non-empty;
- модель возвращает probabilities по классам;
- top predictions сортируются по score;
- если top score >= `confidence_threshold`, статус `known`;
- иначе `uncertain`.

Uncertain flow:
- uncertain кейсы сохраняются в `uncertain_classifications`;
- человек может присвоить `assigned_label`;
- после review создается или переиспользуется topic с source `human_review`.

Topic matching:
- текст эмбеддится;
- сравнивается с активными topic embeddings через cosine distance;
- score = `1 - distance`;
- если classification `known`, topic match status = `not_applicable`;
- если uncertain и top topic score >= 0.35, status = `strong_match`;
- если topics есть, но score ниже threshold, status = `weak_match`;
- если topics нет, status = `no_topics`.

Recommended action:
- `known` → `accept_product_class`;
- `uncertain` + strong topic match → `route_to_dynamic_topic`;
- `uncertain` без strong match → `send_to_human_review`.

CSI-like fields:
- `sentiment` выводится по keyword hits: `negative`, `mixed`, `neutral`;
- `severity` выводится по high severity / negative keywords;
- `csi_score` стартует с 4.0 и уменьшается по sentiment/severity;
- score ограничен диапазоном 1.0–5.0;
- `feedback_channel` маппится из `submitted_via`;
- `customer_segment` назначается стабильным hash bucket по `complaint_id`.

Важно: CSI в проекте синтетически выводится из CFPB complaints, а не загружается как реальный опрос CSI.

# 11. Интеграции

Есть:
- CFPB Socrata HTTP API;
- PostgreSQL/pgvector;
- OpenAI-compatible LLM API через `ChatOpenAI`;
- Hugging Face / sentence-transformers model loading;
- GitHub Actions CI;
- Docker Compose.

Не найдено:
- CRM;
- ERP;
- FTP;
- Email;
- Telegram;
- Google Sheets;
- ClickHouse;
- Oracle;
- Redis;
- Kubernetes;
- Jenkins/GitLab CI/ArgoCD.

# 12. Производительность

Есть:
- batch ingestion из API;
- chunked CSV processing;
- batch loading complaints в БД по 500;
- batch embedding generation;
- batch embedding DB update по 200;
- HNSW pgvector index;
- SQL indexes по frequently filtered/grouped columns;
- `lru_cache` для classifier/search/analytics/topic matcher/settings;
- `pool_pre_ping=True` у SQLAlchemy engine;
- `n_jobs=-1` в LogisticRegression baseline.

# 13. Что можно считать инженерно сложным

- End-to-end pipeline: raw API/CSV → processed dataset → model → embeddings → DB → API.
- Dynamic taxonomy: uncertain classification → human review → topic creation → topic embedding → future topic matching.
- pgvector integration with 384-dim embeddings and HNSW index.
- JSONB storage for model outputs and topic matches.
- LangGraph workflow combining classifier, RAG search, analytics and LLM answer.
- Deterministic fallback when LLM key is absent.
- Runtime metrics based on persisted classification events.
- Alembic schema evolution across several migrations.
- CI with PostgreSQL/pgvector service and migrations.
- Separate evaluation scripts for classifier thresholds and RAG retrieval.

# 14. Что показывает высокий уровень разработчика/аналитика

- Не только notebook/model, а полноценный сервис с API, БД, миграциями, тестами и CI.
- Обработка uncertainty и human-in-the-loop, а не слепое принятие классификации.
- Использование baseline NLP и embedding-based подхода, с сохранением метрик.
- Разделение concerns: `api`, `db`, `ml`, `rag`, `agent`, `data`, `evaluation`.
- Production-like storage: PostgreSQL, JSONB, pgvector, индексы, Alembic.
- Наличие fallback logic для API ingestion и LLM.
- Наличие Makefile для повторяемых операций.
- Наличие runtime observability через `/metrics/classification-runtime`.
- Работа с большими CSV через chunks, а не чтение всего файла целиком.

# 15. Что можно использовать в резюме

✔ реализован FastAPI-сервис для анализа клиентских жалоб и обратной связи  
✔ реализована загрузка данных из CFPB Socrata API и CSV fallback  
✔ разработан ETL pipeline для canonical dataset и processed classification dataset  
✔ обучен TF-IDF + LogisticRegression классификатор продуктовых категорий  
✔ реализована оценка модели через macro F1, weighted F1 и classification report  
✔ реализована threshold evaluation для known/uncertain классификации  
✔ реализован semantic search по жалобам через sentence-transformers и pgvector  
✔ создан HNSW индекс для vector search в PostgreSQL  
✔ реализована динамическая таксономия тем с embeddings  
✔ реализован human-in-the-loop review для низкоуверенных классификаций  
✔ реализовано сохранение classification events с JSONB полями  
✔ реализованы runtime metrics по классификациям и routing decisions  
✔ реализован LangGraph agent для аналитических ответов по жалобам  
✔ реализована LLM-генерация ответов с deterministic fallback  
✔ реализован endpoint для сохранения feedback на ответы агента  
✔ реализованы CSI-like analytics: avg CSI, sentiment, severity, drivers  
✔ настроены Alembic migrations для PostgreSQL схемы  
✔ настроен Docker Compose с PostgreSQL + pgvector  
✔ настроен GitHub Actions CI с migrations, ruff и pytest  
✔ добавлен Makefile для локальных workflow команд  
✔ написаны integration и routing unit tests  

# 16. Какие технологии реально использовались

Языки:
- Python 3.11;
- SQL.

БД:
- PostgreSQL;
- pgvector.

SQL:
- SQLAlchemy ORM/query builder;
- PostgreSQL JSONB;
- PostgreSQL vector extension;
- Alembic migrations.

BI:
- BI-инструментов не найдено.

Python:
- pandas;
- numpy;
- scikit-learn;
- sentence-transformers;
- torch;
- transformers;
- joblib;
- requests.

DevOps:
- Docker Compose;
- GitHub Actions;
- Makefile;
- ruff;
- pytest;
- Alembic.

ETL:
- API ingestion;
- CSV chunk ingestion;
- canonicalization;
- batch DB load;
- embeddings backfill;
- CSI fields backfill.

Фреймворки:
- FastAPI;
- LangGraph;
- LangChain-compatible `ChatOpenAI`.

Инструменты:
- Git;
- Uvicorn;
- Pydantic settings;
- SQLAlchemy;
- psycopg.

# 17. Что можно недооценивать

- JSONB для хранения model outputs и topic matches: это хороший production-style выбор для изменяемых ML payloads.
- HNSW index в PostgreSQL: это не просто “поиск по embeddings”, а уже оптимизированный vector search.
- `known/uncertain` routing: важная ML-product логика, которую часто забывают в демо.
- Human-in-the-loop создание новых тем: прямо соответствует dynamic classes / expandable taxonomy.
- Deterministic fallback без LLM: сервис не ломается без ключа.
- Отдельные runtime classification events: база для мониторинга качества и поведения модели.
- Threshold evaluation: показывает понимание trade-off между coverage и accuracy.
- Разделение integration tests и non-integration routing tests.
- API ingestion с retries и CSV fallback: это ближе к production, чем ручная загрузка файла.
- Alembic chain миграций: демонстрирует управление схемой, а не “создал таблицы руками”.