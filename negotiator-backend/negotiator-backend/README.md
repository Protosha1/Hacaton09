============================================================
NEGOTIATORAI — BACKEND
============================================================
AI-тренажёр деловых переговоров. Пользователь говорит
голосом, ИИ-оппонент отвечает текстом, после сессии — разбор
по SPIN, BATNA и эмоциям.

Версия:      1.1
Дата:        22 сентября 2026
Тестов:      120
Покрытие:    ~85%
============================================================


============================================================
СТЕК
============================================================
- Python 3.12 + FastAPI
- SQLAlchemy (async) + SQLite (готов к PostgreSQL)
- Alembic — миграции
- Qwen LLM (Alibaba Cloud, OpenAI-совместимый API)
- faster-whisper — локальное STT
- JWT — auth (python-jose + bcrypt)
- Docker + docker compose


============================================================
БЫСТРЫЙ СТАРТ (ЛОКАЛЬНО)
============================================================
1. Окружение:

   python -m venv venv #возможно придется сначало удалить папку venv
   venv\Scripts\activate

2. Зависимости:
   pip install -r requirements.txt

4. Миграции:
   alembic upgrade head

5. Демо-данные:
   python seed.py
   python seed_cases.py
   python seed_admin.py

6. Запуск:
   uvicorn app.main:app --host 127.0.0.1 --port 8000

ВАЖНО (Windows + Store-версия Python):
  --reload не работает. Используйте 127.0.0.1, не localhost.
  Swagger: http://127.0.0.1:8000/docs


============================================================
ТЕСТЫ
============================================================
  pytest
  pytest --cov=app --cov-report=term-missing


============================================================
ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
============================================================
  APP_NAME                       Название приложения
  APP_VERSION                    Версия
  PORT                           Порт (8000)
  DATABASE_URL                   Строка подключения к БД
  DASHSCOPE_API_KEY              Ключ Qwen
  LLM_BASE_URL                   Endpoint Qwen
  SECRET_KEY                     Секрет JWT
  ALGORITHM                      HS256
  ACCESS_TOKEN_EXPIRE_MINUTES    10080 (7 дней)
  ADMIN_EMAIL                    Email первого админа
  ADMIN_PASSWORD                 Пароль первого админа
  ADMIN_NAME                     Имя первого админа
  HF_HUB_DISABLE_SYMLINKS        1 (fix для Windows)


============================================================
СТРУКТУРА ПРОЕКТА
============================================================

app/
  api/v1/
    auth.py          Регистрация, логин, онбординг
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

  db/                SQLAlchemy
  models/            8 моделей
    analysis.py
    negotiation.py
    scenario.py
    skill_progress.py
    user.py
    user_added_case.py
  schemas/           Pydantic
  services/          Бизнес-логика
    analysis_service.py
    llm_service.py
    negotiation_service.py
    voice_service.py
  main.py

alembic/             Миграции
tests/               120 тестов
seed.py              3 демо-сценария
seed_cases.py        90 кейсов
seed_admin.py        Создание админа


============================================================
МОДЕЛИ БД
============================================================
  users                  Пользователи + role + status +
                         total_xp + consent_given
  scenarios              Встроенные + админские, со статусом
                         draft/ready/archived
  negotiation_sessions   Сессии (включая interrupted)
  messages               Сообщения user/ai
  analysis_reports       scores, SPIN/BATNA текст,
                         transcript_annotations, xp_earned
  skill_progress         Агрегированные навыки
  user_added_cases       Кейсы, полученные по инвайтам


============================================================
ОСНОВНЫЕ ЭНДПОИНТЫ (КРАТКО)
============================================================
  POST   /auth/register
  POST   /auth/register/admin
  POST   /auth/login
  POST   /auth/login/admin
  GET    /auth/me                    [user]
  POST   /auth/onboarding            [user]

  GET    /scenarios/                 (публичный)
  GET    /scenarios/my               [admin]
  GET    /scenarios/{id}
  POST   /scenarios/                 [admin]
  PUT    /scenarios/{id}             [admin]
  POST   /scenarios/{id}/publish     [admin]
  POST   /scenarios/{id}/archive     [admin]
  DELETE /scenarios/{id}             [admin]

  GET    /invite/{code}              (публичный)
  POST   /invite/{code}              [user]

  POST   /negotiation/start          [user]
  POST   /negotiation/message        [user]
  POST   /negotiation/voice          [user]
  POST   /negotiation/{id}/interrupt [user]
  POST   /negotiation/end            [user]
  GET    /negotiation/analysis/{id}  [user]
  GET    /negotiation/sessions/{uid} [user]
  GET    /negotiation/sessions/{id}/messages [user]
  GET    /negotiation/progress/{uid} [user]
  GET    /negotiation/briefing/{id}  [user]

  GET    /users/{id}/skills          [user]
  GET    /users/{id}/recommendations [user]
  GET    /users/{id}/interrupted-session [user]
  GET    /users/{id}/added-cases     [user]

  GET    /health/


============================================================
КЛЮЧЕВЫЕ ФИЧИ v8
============================================================
- RBAC: user vs admin, взаимная изоляция
- XP + 4 ранга: 0-100, 100-400, 400-700, 700+
- SkillProgress: SPIN, BATNA, эмоции (EMA)
- Interrupted sessions: блок "Вы остановились на"
- Admin-конструктор: 2 шага + publish/archive + invite
- Invite flow: preview без auth, accept с auth
- Аналитика: SPIN/BATNA текст + transcript_annotations
- Briefing: сводка без спойлеров
- Auto-language: LLM отвечает на языке пользователя
- Consent: обязательное consent_given=true


============================================================
ROADMAP
============================================================
ГОТОВО:
  + Auth + RBAC + онбординг
  + 93 сценария (3 legacy + 90 кейсов)
  + STT через Whisper
  + XP, ранги, навыки
  + Аналитика с подсветкой
  + Админ-контур + инвайты
  + Docker



============================================================
ПРОБЛЕМЫ И РЕШЕНИЯ
============================================================
  Cannot connect to Docker daemon
    Запустить Docker Desktop

  port is already allocated
    Остановить локальный uvicorn (Ctrl+C)

  Connection refused
    Использовать 127.0.0.1, не localhost

  Non-UTF-8 code
    Пересохранить файл в UTF-8

  no such column
    alembic upgrade head

  --reload не работает
    Store-версия Python. Установить с python.org

============================================================
КОНЕЦ
============================================================