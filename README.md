# Customer Voice AI

Production ready project for customer feedback analytics.

The system analyzes customer complaint narratives, detects topics, supports dynamically extendable classes, and provides an AI analytics agent over structured and semantic search data.

## CI

The repository includes a GitHub Actions workflow that runs:

- dependency installation;
- Alembic migrations;
- ruff linting;
- pytest test suite.

The CI service uses PostgreSQL with pgvector.

# RU.ver
# Customer Voice AI

Коммерческий проект, примененимый для анализа обратной связи от клиентов.

Система анализирует описания клиентских жалоб, выявляет темы, поддерживает динамическое расширение набора классов и предоставляет AI-агента для аналитики на основе структурированных данных и семантического поиска.

## Планируемые возможности

- Загрузка и обработка данных о жалобах CFPB
- Базовый классификатор на основе классических методов NLP
- Семантический поиск на основе эмбеддингов
- Динамическое расширение тем и классов
- Аналитический агент на базе RAG и LangGraph
- Сервис на FastAPI
- Хранилище PostgreSQL + pgvector
- Контур оценки качества и обратной связи

# Customer Voice AI

Проект, подготовленный к production: анализ клиентской обратной связи, динамическая NLP-классификация, семантический поиск и AI-агент для продуктовой аналитики.

Проект построен вокруг сценария **Голос Клиента**: продуктовым специалистам нужно быстро понимать, на что жалуются клиенты, классифицировать новые обращения, находить возникающие темы и задавать аналитические вопросы по историческим данным.

## Зачем этот проект

`Customer Voice AI` демонстрирует end-to-end ML/LLM-систему, приближенную к требованиям реального сервиса:

- классический NLP baseline для классификации обращений;
- классификацию с учетом неопределенности;
- динамически расширяемую таксономию тем;
- human-in-the-loop процесс ревью;
- хранение данных в PostgreSQL;
- семантический поиск через pgvector;
- агентный workflow на LangGraph;
- генерацию аналитических ответов через LLM;
- детерминированный fallback без LLM-ключа;
- сбор runtime-метрик и пользовательской обратной связи;
- FastAPI-сервис с тестами, миграциями и Docker Compose.

## Демонстрационные данные

В проекте используются тексты потребительских жалоб из датасета CFPB Consumer Complaint Database.

Основные поля:

- ID жалобы;
- дата получения;
- продукт;
- проблема;
- компания;
- штат;
- канал отправки;
- текст обращения.

На основе complaint narratives подготавливается сбалансированный датасет для классификации продуктовой категории.

## Архитектура

```text
Client / Analyst
      |
      v
FastAPI
      |
      +--> Product classifier (TF-IDF + Logistic Regression)
      |
      +--> Dynamic topic matcher (sentence embeddings + pgvector)
      |
      +--> PostgreSQL / pgvector
      |       + complaints
      |       + complaint embeddings
      |       + topics
      |       + uncertain classifications
      |       + classification events
      |       + agent feedback
      |
      +--> LangGraph analytics agent
              + classification
              + semantic search
              + aggregate analytics
              + LLM answer composer
```

## Возможности

### 1. Классификация продукта

Эндпоинт:

```text
POST /comments/classify
```

Сервис возвращает:

- предсказанную продуктовую категорию;
- confidence score;
- top-k предсказаний;
- статус `known` или `uncertain`;
- совпадения с динамическими темами;
- рекомендуемое действие.

Возможные действия:

- `accept_product_class` - принять классификацию продукта;
- `route_to_dynamic_topic` - направить обращение в динамическую тему;
- `send_to_human_review` - отправить на ручное ревью.

### 2. Динамическая таксономия тем

Темы можно создавать вручную или автоматически на основе разобранных uncertain-кейсов.

Эндпоинты:

```text
POST /topics
GET /topics
POST /topics/match
```

Это позволяет расширять набор классов без переобучения основного классификатора.

### 3. Human-in-the-loop review

Классификации с низкой уверенностью сохраняются для проверки человеком.

Эндпоинты:

```text
GET /classifications/uncertain
PATCH /classifications/uncertain/{event_id}/review
```

После ревью система может переиспользовать существующие динамические темы или создавать новые.

### 4. Семантический поиск

Тексты жалоб эмбеддятся и сохраняются в PostgreSQL с pgvector.

Эндпоинт:

```text
POST /search/complaints
```

Для векторного поиска используется HNSW-индекс с cosine distance.

### 5. Аналитический агент на LangGraph

Эндпоинт:

```text
POST /agent/analyze
```

Агент объединяет:

- классификацию запроса;
- поиск похожих жалоб;
- агрегированную аналитику по продуктам и проблемам;
- генерацию ответа через LLM;
- детерминированный fallback, если LLM-ключ не настроен.

### 6. Контур обратной связи

Ответы агента можно оценивать и сохранять для дальнейшего анализа качества.

Эндпоинт:

```text
POST /agent/feedback
```

### 7. Runtime-метрики

Эндпоинт:

```text
GET /metrics/classification-runtime
```

Метрики включают:

- общее число classification events;
- распределение `known` / `uncertain`;
- распределение рекомендованных действий;
- распределение статусов topic matching.

## Технологический стек

- Python 3.11
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- pgvector
- scikit-learn
- sentence-transformers
- LangGraph
- LangChain-compatible chat models
- Docker Compose
- pytest
- ruff

## Локальный запуск

Создайте и активируйте виртуальное окружение:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Установите зависимости:

```bash
make install
```

Запустите PostgreSQL:

```bash
make db-up
```

Примените миграции:

```bash
make migrate
```

Запустите API:

```bash
make api
```

Проверьте healthcheck:

```bash
curl http://127.0.0.1:8000/health
```

## Подготовка данных

Подготовить sample-данные CFPB:

```bash
python -m customer_voice_ai.data.prepare_cfpb_sample
python -m customer_voice_ai.data.build_classification_dataset
```

Обучить baseline-классификатор:

```bash
python -m customer_voice_ai.ml.train_product_baseline
```

Загрузить жалобы в PostgreSQL:

```bash
make load-complaints
```

Собрать локальные embedding artifacts:

```bash
python -m customer_voice_ai.rag.build_local_index
```

Загрузить эмбеддинги в PostgreSQL:

```bash
make load-embeddings
```

Обновить эмбеддинги тем:

```bash
make backfill-topics
```

## Проверка качества

```bash
make check
```

Текущие проверки включают:

- ruff linting;
- smoke-тесты API;
- smoke-тест LangGraph-агента.

## Примеры API-запросов

### Классифицировать обращение

```bash
curl -X POST "http://127.0.0.1:8000/comments/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Face ID login fails and the banking app does not let customers see balances.",
    "top_k": 3,
    "confidence_threshold": 0.95,
    "include_topic_matches": true
  }'
```

### Найти похожие жалобы

```bash
curl -X POST "http://127.0.0.1:8000/search/complaints" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "debt collector calling about a debt I do not owe",
    "top_k": 3
  }'
```

### Задать вопрос аналитическому агенту

```bash
curl -X POST "http://127.0.0.1:8000/agent/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Why are customers complaining about debt collection?",
    "top_k": 3
  }'
```

## Конфигурация LLM

Проект поддерживает OpenAI-compatible chat providers.

Переменные окружения:

```env
LLM_API_KEY=
LLM_BASE_URL=
LLM_MODEL=gpt-4.1-mini
```

Если LLM-ключ не задан, агент использует детерминированный composer ответа.

## Текущие baseline-метрики

Начальный классификатор `TF-IDF + Logistic Regression`:

- Macro F1: примерно `0.77`;
- Weighted F1: примерно `0.81`.

Threshold evaluation показывает trade-off между coverage и precision для известных классификаций.

## Production-подход

Проект намеренно разделяет:

- training artifacts;
- runtime API;
- database migrations;
- vector search;
- feedback capture;
- dynamic taxonomy updates;
- runtime observability.

Кодовая база обрезана, но границы компонентов выбраны так, чтобы являться базовым устройством production ML-сервиса.
