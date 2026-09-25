============================================================
NEGOTIATORAI - BACKEND
============================================================
AI-тренажёр деловых переговоров.
Пользователь говорит голосом, ИИ-оппонент отвечает текстом,
после сессии - разбор по SPIN, BATNA и эмоциям.

Версия:      1.3
Дата:        26 сентября 2026
Тестов:      157
Стек:        Python 3.12 + FastAPI + SQLAlchemy (async)
============================================================


============================================================
СТЕК
============================================================
- Python 3.12 + FastAPI
- SQLAlchemy (async) + SQLite (готов к PostgreSQL)
- Alembic - миграции
- Qwen LLM (Alibaba Cloud, OpenAI-совместимый API)
- faster-whisper (модель small) - локальное STT
- JWT - auth (python-jose + bcrypt)
- Docker + docker compose


============================================================
БЫСТРЫЙ СТАРТ (ЛОКАЛЬНО)
============================================================
1. Виртуальное окружение:
   python -m venv venv
   venv\Scripts\activate          (Windows)
   source venv/bin/activate       (Mac/Linux)

2. Зависимости:
   pip install -r requirements.txt

3. Скопировать .env:
   copy .env.example .env


5. Миграции:
   alembic upgrade head


7. Запуск:
   uvicorn app.main:app --host 127.0.0.1 --port 8000

8. Открыть:
   http://127.0.0.1:8000/docs


ВАЖНО (Windows + Python из Microsoft Store):
  --reload может не работать. Используйте 127.0.0.1, не localhost.
  Если нужен --reload - установите Python с python.org.

ВАЖНО (кодировка файлов):
  Все .py файлы должны быть в UTF-8 без BOM.
  В VS Code: File -> Save with Encoding -> UTF-8
  Настройка на будущее: "files.encoding": "utf8"

 Демо-данные:
   python seed.py                 # 3 встроенных сценария
   python seed_cases.py           # 90 кейсов по 6 категориям
   python seed_admin.py           # админ из .env


============================================================
БЫСТРЫЙ СТАРТ (DOCKER)
============================================================
1. Скопировать .env и заполнить (см. выше).

2. Собрать и запустить:
   docker compose up -d --build

3. Первый раз - миграции и данные:
   docker compose exec backend alembic upgrade head
   docker compose exec backend python seed.py
   docker compose exec backend python seed_cases.py
   docker compose exec backend python seed_admin.py

4. Открыть:
   http://localhost:8000/docs

База и кэш Whisper хранятся в named volume `appdata`,
поэтому переживают пересборку контейнера.


============================================================
ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
============================================================
ОБЯЗАТЕЛЬНЫЕ:
  SECRET_KEY                     Секрет JWT. Минимум 32 символа.
  ADMIN_PASSWORD                 Пароль первого админа. Минимум 12 символов.
  DASHSCOPE_API_KEY              Ключ Qwen для вызовов LLM.

ОПЦИОНАЛЬНЫЕ (application):
  APP_NAME                       Название приложения (default: NegotiatorAI)
  APP_VERSION                    Версия (default: 0.1.0)
  PORT                           Порт сервера (default: 8000)
  DATABASE_URL                   Строка подключения (default: SQLite)
  LLM_BASE_URL                   Endpoint Qwen (default: международный регион)
  ALGORITHM                      HS256
  ACCESS_TOKEN_EXPIRE_MINUTES    Время жизни токена (default: 10080 = 7 дней)
  CORS_ORIGINS                   Список origin через запятую

ОПЦИОНАЛЬНЫЕ (admin):
  ADMIN_EMAIL                    Email первого админа
  ADMIN_NAME                     Имя первого админа

  ADMIN_REGISTRATION_ENABLED     True | False. Публичная регистрация админа.
                                 True - как в ТЗ v8 (открытая)
                                 False - только через seed_admin.py

  ADMIN_REGISTRATION_CODE        Если задан - требуется при регистрации админа.
                                 Раздаётся только тем, кому нужно.

ОПЦИОНАЛЬНЫЕ (cleanup):
  SESSION_CLEANUP_INTERVAL_SECONDS  Как часто проверять зависшие сессии (default: 300)
  SESSION_TIMEOUT_MINUTES           Через сколько минут без активности
                                    переводить сессию в interrupted (default: 30)

ОПЦИОНАЛЬНЫЕ (voice):
  HF_HUB_DISABLE_SYMLINKS       1 (fix для Windows)
  HF_HOME                       Путь к кэшу Whisper


============================================================
ТЕСТЫ
============================================================
  pytest
  pytest -v
  pytest --cov=app --cov-report=term-missing

Покрытие основных сценариев:
  - Auth, RBAC, онбординг, consent
  - Все эндпоинты negotiation (start, message, voice, end, analysis)
  - Admin-CRUD сценариев, publish, archive, invite
  - Rate limiting на регистрацию админа
  - Приватность: админ не видит чужие результаты
  - SPIN/BATNA, транскрипт-аннотации, XP, навыки
  - Фоновый авто-таймаут сессий


============================================================
СТРУКТУРА ПРОЕКТА
============================================================

app/
  api/v1/
    auth.py          Регистрация, логин, онбординг, rate limit
    health.py        Healthcheck
    invites.py       Приглашения
    negotiation.py   Переговоры, история, аналитика, briefing
    scenarios.py     Сценарии (публичные + админ-CRUD)
    users.py         Навыки, рекомендации, прерванные, added-cases

  core/
    config.py        Настройки
    error_handlers.py Обработчики ошибок
    security.py      Bcrypt + JWT
    skills.py        EMA-обновление навыков
    xp.py            XP и ранги
    rate_limit.py    In-memory rate limiter

  db/                SQLAlchemy
  models/            7 моделей
  schemas/           Pydantic
  services/
    analysis_service.py      LLM-анализ сессии
    llm_service.py           Вызовы Qwen
    negotiation_service.py   Логика диалога
    voice_service.py         STT через Whisper
    retry.py                 Retry на внешние вызовы
    session_cleanup.py       Фоновая задача авто-таймаута

  main.py

alembic/             Миграции
tests/               157 тестов
seed.py              3 демо-сценария
seed_cases.py        90 кейсов
seed_admin.py        Создание админа


============================================================
МОДЕЛИ БД
============================================================
  users                  Пользователи + role + status +
                         total_xp + consent_given
  scenarios              Встроенные + админские, со статусом
                         draft/ready/archived + invite_code
  negotiation_sessions   Сессии (ongoing/finished/interrupted)
  messages               Сообщения user/ai
  analysis_reports       scores, SPIN/BATNA текст,
                         transcript_annotations, xp_earned
  skill_progress         Агрегированные навыки по метрикам
  user_added_cases       Кейсы, полученные по инвайтам


============================================================
ОСНОВНЫЕ ЭНДПОИНТЫ
============================================================
  POST   /auth/register                 [public]
  POST   /auth/register/admin           [public, rate limited]
  POST   /auth/login                    [public]
  POST   /auth/login/admin              [public]
  GET    /auth/me                       [user | admin]
  POST   /auth/onboarding               [user]

  GET    /scenarios/                    [public]
  GET    /scenarios/my                  [admin]
  GET    /scenarios/{id}                [public, без спойлеров]
  GET    /scenarios/{id}/admin          [admin, со спойлерами]
  POST   /scenarios/                    [admin]
  PUT    /scenarios/{id}                [admin]
  POST   /scenarios/{id}/publish        [admin]
  POST   /scenarios/{id}/archive        [admin]
  DELETE /scenarios/{id}                [admin]

  GET    /invite/{code}                 [public]
  POST   /invite/{code}                 [user]

  POST   /negotiation/start             [user]
  POST   /negotiation/message           [user]
  POST   /negotiation/voice             [user]
  POST   /negotiation/{id}/interrupt    [user]
  POST   /negotiation/end               [user]
  GET    /negotiation/analysis/{id}     [user]
  GET    /negotiation/sessions/{uid}    [user]
  GET    /negotiation/sessions/{id}/messages [user]
  GET    /negotiation/progress/{uid}    [user]
  GET    /negotiation/briefing/{id}     [user]

  GET    /users/{id}/skills             [user]
  GET    /users/{id}/recommendations    [user]
  GET    /users/{id}/interrupted-session [user]
  GET    /users/{id}/added-cases        [user]

  GET    /health/                       [public]


============================================================
КЛЮЧЕВЫЕ ФИЧИ v8
============================================================
- RBAC: user vs admin, взаимная изоляция (FR-19)
- XP + 4 ранга: 0-100, 100-400, 400-700, 700+ (FR-39)
- SkillProgress: SPIN, BATNA, эмоции через EMA (FR-24)
- Interrupted sessions: блок "Вы остановились на" (FR-21)
- Admin-конструктор: Шаг 1 + Шаг 2, publish, archive (FR-43..47)
- Invite flow: preview без auth, accept с auth (FR-48, FR-49)
- Аналитика: SPIN/BATNA текст + transcript_annotations (FR-36, FR-37)
- Briefing: сводка без спойлеров (FR-15)
- Auto-language: LLM отвечает на языке пользователя
- Consent: обязательное consent_given=true (v8 privacy)
- Rate limiting на /auth/register/admin (5 регистраций в час с IP)
- Retry на вызовы Qwen (3 попытки с exponential backoff)
- Фоновый авто-таймаут: сессия без активности >30 мин -> interrupted
- Разделение спойлеров: публичный /scenarios/{id} без opponent_goal,
  tactics, concession_limits; админский /scenarios/{id}/admin со всем


============================================================
ОТКЛОНЕНИЯ ОТ ТЗ v8
============================================================
1. TTS не реализован.
   Ввод голосовой (Whisper STT), вывод текстовый.
   FR-32 требует голосовой вывод - решение отложено.
   Пользователь говорит, ИИ отвечает текстом на экране.

2. Статусы сессии упрощены.
   ТЗ: created -> briefing_ready -> in_progress -> completed -> analyzed.
   Код: ongoing | finished | interrupted.
   Промежуточные статусы не нужны фронту на текущем этапе.

3. Регистрация админа публичная (как в ТЗ v8).
   Компенсируется тремя гейтами:
   - ADMIN_REGISTRATION_ENABLED (общий выключатель)
   - ADMIN_REGISTRATION_CODE (опциональный секретный код)
   - Rate limiting (5 в час с одного IP)


============================================================
ПРОБЛЕМЫ И РЕШЕНИЯ
============================================================
  Pydantic: SECRET_KEY required
    Заполните SECRET_KEY в .env (минимум 32 символа)

  seed_admin: ADMIN_PASSWORD too short
    Заполните ADMIN_PASSWORD в .env (минимум 12 символов)

  alembic: no such column
    alembic upgrade head

  sqlalchemy.exc.IntegrityError: UNIQUE constraint failed
    alembic upgrade head - возможно, миграции не применены

  Connection refused
    Использовать 127.0.0.1, не localhost

  --reload не работает
    Python из Microsoft Store. Установить с python.org.

  Non-UTF-8 code в .py файле
    Файл сохранён в Windows-1251. Пересохранить в UTF-8:
    VS Code: File -> Save with Encoding -> UTF-8
    Настройка на будущее: "files.encoding": "utf8"

  Too many admin registrations
    Rate limiter: 5 регистраций админа в час с одного IP.
    Подождать или изменить лимит в app/core/rate_limit.py.

  Whisper долго грузится на первом запросе
    Модель загружается при старте сервера (warmup).
    Первый запрос к /voice должен быть мгновенным.
    Если всё равно тормозит - смените модель в voice_service.py
    с "small" на "base" (~150 МБ вместо ~500 МБ).


============================================================
TIPS
============================================================
Проверить целостность проекта:
  python audit.py

Проверить все .py файлы на компиляцию и кодировку:
  python -m compileall app tests alembic

Сгенерировать TypeScript-типы для фронта:
  npx openapi-typescript http://127.0.0.1:8000/openapi.json -o src/api-types.ts

Отозвать DashScope-ключ (если утёк):
  https://dashscope.console.aliyun.com/


============================================================
ЛИЦЕНЗИЯ И КОНТРИБЬЮЦИЯ
============================================================
Приватный проект. Контрибьюция - через PR в основную ветку.
Перед коммитом: pytest -v && python audit.py.


============================================================
КОНЕЦ
============================================================