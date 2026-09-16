# NegotiatorAI — Backend

AI-тренажёр деловых переговоров. Пользователь выбирает сценарий, ведёт голосовой диалог с ИИ-оппонентом и получает разбор своей работы.

## Стек

- **Python 3.12** + **FastAPI**
- **SQLAlchemy** (async) + **SQLite** (готов к PostgreSQL)
- **Alembic** — миграции
- **Qwen LLM** (Alibaba Cloud, OpenAI-совместимый API)
- **faster-whisper** — локальное распознавание речи (STT)
- **JWT** — аутентификация (python-jose + bcrypt)
- **Docker** + **Docker Compose**

## Быстрый старт (локально, без Docker)

### 1. Виртуальное окружение

```cmd
cd путь до коренной папки
python -m venv venv
venv\Scripts\activate
```

### 2. Зависимости

```cmd
pip install -r requirements.txt
```

### 3. `.env` из шаблона

```cmd
copy .env.example .env
```

Заполните ключи.

### 4. Миграции

```cmd
alembic upgrade head
```

### 5. Демо-данные

```cmd
python seed.py
python seed_cases.py
```

### 6. Запуск сервера

⚠️ **На Windows с Python из Microsoft Store** флаг `--reload` не работает. Запускайте так:

```cmd
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

⚠️ **Открывайте Swagger через `127.0.0.1`, не `localhost`** — иначе IPv6 может не найти сервер:  
👉 http://127.0.0.1:8000/docs

---

## Тесты

```cmd
pytest
```

С покрытием:

```cmd
pytest --cov=app --cov-report=term-missing
```

**Статус:** 19 тестов, покрытие ~73%. - пиздеж, это старый результат. Сейчас все хуже

---

## Переменные окружения

| Переменная | Описание | Пример |
|-----------|----------|--------|
| `APP_NAME` | Название приложения | `NegotiatorAI` |
| `APP_VERSION` | Версия | `0.1.0` |
| `PORT` | Порт сервера | `8000` |
| `DATABASE_URL` | Строка подключения к БД | `sqlite+aiosqlite:///./app.db` |
| `DASHSCOPE_API_KEY` | API-ключ Qwen | `sk-...` |
| `LLM_BASE_URL` | Endpoint Qwen | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |
| `SECRET_KEY` | Секрет для JWT | random 32+ chars |
| `ALGORITHM` | Алгоритм JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни токена | `10080` (7 дней) |
| `HF_HUB_DISABLE_SYMLINKS` | Fix для Windows (Whisper) | `1` |

---

## Структура проекта

```
app/
├── api/v1/                    REST-эндпоинты
│   ├── auth.py                Регистрация, логин, онбординг
│   ├── health.py              Healthcheck
│   ├── negotiation.py         Переговоры, история, прогресс
│   └── scenarios.py           Сценарии
├── core/                      Конфиг и безопасность
│   ├── config.py              Настройки из .env
│   ├── error_handlers.py      Глобальные обработчики
│   └── security.py            Bcrypt + JWT
├── db/                        SQLAlchemy
│   ├── base.py                Импорт всех моделей для Alembic
│   └── session.py             Движок, сессии, get_db
├── models/                    SQLAlchemy-модели
│   ├── analysis.py            AnalysisReport
│   ├── negotiation.py         NegotiationSession, Message
│   ├── scenario.py            Scenario
│   └── user.py                User
├── schemas/                   Pydantic-схемы
├── services/                  Бизнес-логика
│   ├── analysis_service.py    Анализ через Qwen
│   ├── llm_service.py         Обёртка над Qwen API
│   ├── negotiation_service.py Ядро переговоров
│   └── voice_service.py       Whisper STT
└── main.py                    Точка входа

alembic/                       Миграции БД
tests/                         pytest-тесты
seed.py                        Демо-данные (3 базовых сценария)
seed_cases.py                  90 кейсов из документа
refresh_cases.py               Пересоздание case-* сценариев
```

---

## Сценарии

Всего **93**:

| ID | Категория | Описание |
|----|-----------|----------|
| `scenario-1..3` | (demo) | Tough Buyer, Friendly Partner, Manipulator |
| `case-1..15` | `management` | Общение с руководством |
| `case-16..30` | `hiring` | Собеседования и найм |
| `case-31..45` | `team` | Управление командой |
| `case-46..60` | `colleagues` | Взаимодействие с коллегами |
| `case-61..75` | `clients` | Обслуживание клиентов |
| `case-76..90` | `partners` | Переговоры с партнёрами |

---

## Основные эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/v1/auth/register` | Регистрация |
| POST | `/api/v1/auth/login` | Логин |
| GET | `/api/v1/auth/me` | Профиль 🔒 |
| POST | `/api/v1/auth/onboarding` | Онбординг 🔒 |
| GET | `/api/v1/scenarios/` | Список сценариев (с фильтром `?category=`) |
| GET | `/api/v1/scenarios/{id}` | Детали сценария |
| POST | `/api/v1/negotiation/start` | Начать сессию 🔒 |
| POST | `/api/v1/negotiation/message` | Отправить текст 🔒 |
| POST | `/api/v1/negotiation/voice` | Отправить голос 🔒 |
| POST | `/api/v1/negotiation/end?session_id=` | Завершить + анализ 🔒 |
| GET | `/api/v1/negotiation/analysis/{session_id}` | Сохранённый анализ 🔒 |
| GET | `/api/v1/negotiation/sessions/{user_id}` | История сессий 🔒 |
| GET | `/api/v1/negotiation/sessions/{session_id}/messages` | Переписка 🔒 |
| GET | `/api/v1/negotiation/progress/{user_id}` | Прогресс по метрикам 🔒 |
| GET | `/api/v1/health/` | Healthcheck |

🔒 — требует `Authorization: Bearer <token>`.

---

## Ключевые фичи

### Голосовой ввод

Пользователь **говорит** в микрофон → Whisper распознаёт → LLM отвечает **текстом**. TTS не реализован.

### Сценарий влияет на ИИ

Каждый сценарий содержит:
- `opponent_character` — характер
- `opponent_goal` — цель
- `concession_limits` — пределы уступок
- `tactics` — тактики
- `default_relationship` / `default_power_balance` — дефолтный контекст

Всё это подставляется в `system_prompt` для Qwen.

### 3 уровня сложности

- `beginner` — ИИ мягкий, даёт подсказки
- `practitioner` — фирменный стиль
- `expert` — ИИ жёсткий, давит

### Аналитика (FR-19, FR-10)

После `/end` Qwen возвращает:
- `goal_achieved` — yes/no/partial
- 6 числовых оценок (SPIN, BATNA, эмоции и т.д.)
- `strengths`, `weaknesses`, `suggestions`
- `full_report`

### Авто-язык

LLM **отвечает на языке пользователя**: написали по-русски → ответ по-русски.

---

## Для фронтендера

Полный контракт API → **[API_CONTRACT.md](./API_CONTRACT.md)**.

Там:
- Все эндпоинты с примерами
- Форматы запросов/ответов
- Коды ошибок
- Примеры кода на JS
- Roadmap и ограничения

### Генерация TypeScript-типов

```bash
npx openapi-typescript http://127.0.0.1:8000/openapi.json -o src/api-types.ts
```

---

## Troubleshooting

### `Cannot connect to Docker daemon`

Docker Desktop не запущен. Откройте его, дождитесь `Engine running`.

### `port is already allocated`

Порт 8000 занят — остановите локальный uvicorn (`Ctrl+C`).

### `Connection refused` при curl

Сервер запущен на `--host 127.0.0.1`, а вы обращаетесь к `localhost`. Используйте `127.0.0.1` в URL.

### `Non-UTF-8 code starting with '\x...'`

Файл сохранён в Windows-1251. В VS Code: правый нижний угол → **Save with Encoding → UTF-8**.

### `--reload` не работает

Python из Microsoft Store конфликтует с `--reload` на Windows. Решения:
- Запускать вручную без `--reload` (перезапускать при изменениях).
- Установить Python с [python.org](https://www.python.org/).

### `no such column: ...`

Миграция не применена: `alembic upgrade head`.

---

## Roadmap

### Готово

- ✅ Аутентификация (JWT)
- ✅ Онбординг + профиль
- ✅ 93 сценария в 6 категориях
- ✅ Голосовой ввод (Whisper)
- ✅ Аналитика с SPIN/BATNA/эмоциями
- ✅ Прогресс по метрикам
- ✅ История тренировок
- ✅ Docker

### Не реализовано

- ❌ TTS (озвучка ответов ИИ)
- ❌ Транскрипция с подсветкой неудачных фраз
- ❌ Рекомендации кейсов (`/scenarios/recommended`)
- ❌ Согласие на обработку данных при регистрации
- ❌ Флаг `interrupted` для прерванных сессий

Аня, я ебал это делать. MVP это нахер не всралось. Я это пишу в 02.55 ночи, а сегодня на сборы военные.
Пожелаю удачи это все понять. Такое чувство, что ты попытаешься меня придушить после таких инструкций

---

