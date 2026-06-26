# 1

Да. Это **Customer Voice AI** — учебно-демонстрационная, но production-style платформа для анализа клиентской обратной связи и обращений.

Если коротко: система берет сырые клиентские жалобы/комментарии, превращает их в структурированную аналитику, умеет классифицировать новые обращения, находить похожие кейсы, выявлять новые темы и давать продуктовым специалистам ответы через AI-агента.

Что внутри по смыслу:

- **Классификация обращений**: модель определяет продуктовую категорию жалобы, например `Debt collection`, `Credit card`, `Mortgage`.
- **Uncertainty handling**: если модель не уверена, она не притворяется, что знает ответ, а помечает кейс как `uncertain`.
- **Динамические темы**: uncertain-кейсы попадают в review queue; человек может назначить новый класс/тему, и система добавит ее в базу знаний.
- **Few-shot topic matching**: новые комментарии сравниваются с динамическими темами через embeddings.
- **RAG / semantic search**: обращения лежат в PostgreSQL + pgvector, можно искать похожие жалобы по смыслу.
- **LangGraph agent**: агент объединяет классификацию, поиск, агрегаты и LLM-компоновку ответа.
- **CSI analytics**: система считает CSI-like score, sentiment, severity, показывает summary, trends и drivers падения удовлетворенности.
- **Feedback loop**: ответы агента можно оценивать, feedback сохраняется в БД.
- **Runtime metrics**: есть метрики по классификационному потоку: known/uncertain, recommended actions, topic match status.
- **Production-инфраструктура**: FastAPI, PostgreSQL, pgvector, Alembic, Docker Compose, Makefile, тесты, lint, CI.

Главная ценность проекта: он показывает не просто “я умею вызвать LLM”, а умение собрать ML/LLM-систему вокруг реального бизнес-процесса: от данных и моделей до API, БД, метрик, human-in-the-loop и расширяемой таксономии.

# 2
Да, тут надо вообще уйти от “LangGraph, pgvector, embeddings”. Для директора это не продукт, это внутренности. Продукт здесь такой:

**Это система, которая превращает тысячи разрозненных клиентских жалоб в список конкретных продуктовых проблем, их масштаба и приоритета.**

Не “ИИ-агент”, а **радар клиентской боли**.

Если говорить менеджерски:

> Customer Voice AI помогает продуктовым командам быстро понять, что именно ломает клиентский опыт, насколько проблема массовая, где она растет и какие действия требуют внимания. Система не просто отвечает на вопросы, а собирает обратную связь в управляемую карту проблем: известные темы, новые сигналы, причины падения удовлетворенности и примеры реальных обращений.

Чем это отличается от массы “ИИ-агентов”:

**1. Не чат ради чата, а управленческий контур**

Обычный AI-агент отвечает на вопрос.  
Этот продукт строит процесс:

- принять новый фидбэк;
- понять тему;
- оценить уверенность;
- найти похожие обращения;
- подсветить новые проблемы;
- передать спорные случаи человеку;
- обновить базу тем;
- показать метрики и динамику.

То есть это не “умный ассистент”, а система принятия продуктовых решений.

**2. Он умеет признавать неизвестное**

Большинство демо с ИИ красиво отвечают даже тогда, когда не знают.  
Здесь ценность в другом: если система не уверена, она не маскирует это красивым текстом, а отправляет случай в разметку и помогает создать новую тему.

Для бизнеса это важно: новые проблемы клиентов часто сначала не попадают в старую классификацию. Например раньше не было темы “Face ID login failure”, а потом она начала появляться. Система умеет это поймать.

**3. Он превращает шум в приоритизацию**

Бизнесу не нужно читать 10 000 отзывов. Ему нужно знать:

- какие 5 проблем сейчас сильнее всего портят клиентский опыт;
- какая тема растет;
- где больше всего негатива;
- какие продукты проседают;
- есть ли новые проблемы, которых не было в справочнике;
- на чем сфокусировать команду на этой неделе.

Это уже не “аналитика ради аналитики”, а вход в roadmap, backlog и операционные решения.

**4. Он дает доказательства, а не просто мнение ИИ**

Ответы агента опираются на реальные обращения и агрегаты. То есть менеджер может увидеть не только “пользователи недовольны”, а:

- какая тема;
- сколько похожих обращений;
- какие продукты затронуты;
- насколько низкий CSI;
- примеры конкретных жалоб;
- почему система так решила.

Это снижает риск “ИИ придумал красивую историю”.

**5. Он накапливает организационную память**

Каждая новая тема, ручная проверка, feedback на ответ, классификационное событие сохраняются. Со временем это становится базой знаний о клиентских проблемах.

Не одноразовый чат, а продукт, который обучается на работе команды.

Я бы для директора формулировал так:

> Это не очередной AI-чат, а система раннего обнаружения клиентских проблем. Она автоматически группирует обращения, показывает причины падения удовлетворенности, находит новые темы, подтверждает выводы реальными жалобами и помогает продуктовым командам быстрее переводить обратную связь в решения.

Еще более коротко для резюме/презентации:

> Разработал Customer Voice AI — платформу, которая превращает клиентские обращения в карту продуктовых проблем: классифицирует фидбэк, выявляет новые темы, показывает драйверы падения CSI и дает AI-ассистенту отвечать с опорой на реальные обращения и метрики.

А если нужен “интеллигентный кликбейт”:

> Не чат-бот, а радар клиентской боли: система находит, объясняет и приоритизирует проблемы в клиентском фидбэке до того, как они превращаются в продуктовый пожар.

Мой любимый вариант для нетехнической аудитории:

> Customer Voice AI — это слой управления клиентской обратной связью: он превращает поток жалоб и комментариев в понятную карту проблем, их влияния на удовлетворенность и следующих действий для продуктовой команды. Главное отличие от обычного AI-ассистента — система не просто “отвечает”, а ведет полный цикл: обнаружение темы, проверка уверенности, human review, обновление базы знаний и измерение качества решений.

# 3
Для ML/DS аудитории я бы описывал не как “я сделал супер-агента”, а как **прикладной ML system design вокруг Voice of Customer**. Спокойно, инженерно, с уважением к ограничениям.

Вот хороший вариант:

> Customer Voice AI — pet/project-демо production-style пайплайна для Voice of Customer аналитики. Я собрал end-to-end систему вокруг CFPB complaint narratives: классический TF-IDF + Logistic Regression baseline, embedding-based retrieval в pgvector, uncertainty-aware классификацию, human-in-the-loop расширение таксономии и LangGraph-агента, который отвечает с опорой на SQL-агрегаты и найденные обращения.  
>  
> Основной фокус был не на “магии LLM”, а на ML lifecycle: воспроизводимая подготовка данных, baseline/eval reports, thresholds, runtime events, feedback loop, Alembic migrations, FastAPI API, Docker Compose, tests/ruff/CI. Отдельно реализовал dynamic topics: low-confidence кейсы уходят в review, после разметки создают новые темы с embeddings, и последующие комментарии могут матчиться к ним без переобучения основного классификатора.

Если надо чуть короче для GitHub/резюме:

> Built a production-style Voice of Customer ML/LLM system on CFPB complaint narratives: TF-IDF baseline classifier, pgvector semantic retrieval, uncertainty-aware routing, human-in-the-loop dynamic topics, CSI-like analytics, LangGraph agent, feedback loop, and runtime metrics.  
> The emphasis is on practical ML engineering rather than a “chatbot demo”: data prep, evaluation reports, thresholds, migrations, API contracts, tests, Docker/CI, and clear fallback paths when LLM confidence or model confidence is insufficient.

Если по-русски и без пафоса:

> Сделал production-style демо системы Voice of Customer аналитики на CFPB complaint narratives. В проекте есть классический NLP baseline, embedding retrieval через pgvector, классификация с uncertainty handling, human-in-the-loop расширение тем, CSI-like аналитика, LangGraph-агент и feedback/runtime metrics.  
> Главная идея — показать не “обертку над LLM”, а полный ML-инженерный контур: подготовка данных, метрики, thresholding, хранение событий, миграции, API-контракты, тесты, Docker/CI и fallback-логика.

А если хочется звучать как “свой” в ML/DS, я бы добавил такую честную оговорку:

> Я сознательно начал с сильного классического baseline и простых, проверяемых решений. TF-IDF + LogReg оказался конкурентным для product classification, а sentence-transformers использовал там, где они дают больше ценности: retrieval, topic matching и dynamic taxonomy. LLM используется как answer composer поверх evidence, а не как источник истины.

Вот это прям хорошо. Потому что ML-аудитория любит, когда человек не делает вид, что LLM заменил всё.

Можно еще так, более “архитектурно”:

> В проекте разделены offline и online части: offline data prep/training/evaluation, online FastAPI inference, pgvector search, event logging, human review и monitoring endpoints. Это позволило показать не только модель, но и жизненный цикл: от baseline и threshold analysis до динамического обновления таксономии и анализа runtime-событий.

Самая сильная формулировка для ML/DS собеседования:

> Для меня это был эксперимент в том, как правильно собрать LLM-enabled ML system: оставить классические модели там, где они надежны и интерпретируемы; использовать embeddings для retrieval и few-shot topic matching; ограничить LLM ролью генерации ответа по evidence; и обязательно добавить uncertainty, eval, feedback и audit trail.

Я бы использовал именно ее устно. Она показывает зрелость. Тут есть вкус: не “я прикрутил ИИ”, а “я думал о границах компонентов”.

# 4
Да, вот это правильный вопрос. Сейчас проект уже production-like, но он все еще **CFPB-oriented under the hood**. Чтобы он стал реально клиентским/многоисточниковым, нужно отделить **доменную модель Customer Voice** от конкретного источника данных.

Я бы доделывал в 6 направлениях.

**1. Source adapters**

Сейчас у нас фактически есть CFPB ingestion. Нужно сделать интерфейс:

```python
class FeedbackSourceAdapter:
    def fetch(self) -> Iterable[RawFeedbackRecord]: ...
    def normalize(self, raw) -> CanonicalFeedbackRecord: ...
```

И реализации:

- `CfpbSocrataAdapter`
- `CsvFeedbackAdapter`
- `ZendeskAdapter`
- `IntercomAdapter`
- `SurveyMonkeyAdapter`
- `GoogleSheetsAdapter`
- `S3CsvAdapter`
- `PostgresSourceAdapter`

Тогда новый клиент = новый adapter, а не переписывание pipeline.

**2. Canonical schema**

Нужна нейтральная схема вместо CFPB-полей:

```text
feedback_id
source_system
source_record_id
received_at
customer_id
customer_segment
channel
product
service
topic
raw_text
language
rating
csi_score
nps_score
sentiment
severity
metadata JSONB
```

Все специфичные поля клиента складывать в `metadata JSONB`, а не плодить колонки под каждого.

**3. Dataset/source registry**

Добавить таблицу `feedback_sources`:

```text
source_id
name
source_type
client_name / tenant_id
config JSONB
status
created_at
last_sync_at
```

И таблицу `ingestion_runs`:

```text
run_id
source_id
started_at
finished_at
status
rows_read
rows_inserted
rows_failed
error_message
```

Это сразу делает ingestion наблюдаемым и многоисточниковым.

**4. Multi-tenant / client context**

Если проект под разных клиентов, нужен хотя бы `tenant_id` почти везде:

- complaints / feedback records;
- topics;
- classification events;
- feedback;
- metrics;
- agent requests.

Иначе темы одного клиента начнут матчиться на обращения другого.

Минимально:

```text
tenant_id
```

в ключевых таблицах + фильтрация во всех repository/query.

**5. Config-driven taxonomy**

Для разных клиентов разные таксономии:

- продукты;
- каналы;
- темы;
- severity rules;
- CSI/NPS mapping;
- языки;
- стоп-слова;
- threshold.

Это лучше хранить в БД:

```text
taxonomy_versions
topic_sets
classification_thresholds
client_rules
```

Тогда клиент А может иметь threshold `0.55`, клиент Б — `0.72`, а клиент В — кастомные темы.

**6. Ingestion API / admin API**

Сейчас ingestion — CLI. Для клиентского использования нужен API:

```text
POST /sources
GET /sources
POST /sources/{source_id}/sync
GET /ingestion-runs
POST /feedback/import
```

Для CSV:

```text
POST /feedback/import-file
```

Для raw JSON:

```text
POST /feedback/import
```

Тогда можно подключать клиента без доступа к серверу.

**Что я бы делал первым**

Я бы не переписывал все сразу. Самый сильный следующий production-рефактор:

1. Переименовать `Complaint` в `FeedbackRecord` или добавить новую таблицу `feedback_records`.
2. Добавить `tenant_id`, `source_system`, `source_record_id`, `raw_text`, `metadata JSONB`.
3. Сделать `SourceAdapter` interface.
4. Переписать CFPB ingestion как один adapter.
5. Добавить CSV adapter для произвольных клиентских CSV через mapping config.

Например клиентский CSV mapping:

```yaml
source_type: csv
tenant_id: demo_bank
columns:
  id: response_id
  text: comment
  received_at: created_at
  product: product_name
  rating: csi
  channel: survey_channel
metadata:
  - region
  - branch
  - manager_id
```

Вот тогда проект становится реально клиентским: чтобы подключить нового клиента, ты не меняешь ML/RAG/agent, ты меняешь mapping config или adapter.

**Самая важная формулировка**

Сейчас у нас: “система анализа CFPB complaints”.

После доработки должно стать:

> configurable Voice of Customer platform with pluggable data source adapters and tenant-specific taxonomies.

Это уже звучит как продукт, а не учебный проект.