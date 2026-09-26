# Как запустить NegotiatorAI (frontend + backend)

Бэкенд не менялся — используются те инструкции, что уже были в репозитории
(`negotiator-backend/SETUP_FOR_FRONTEND.md`). Ниже — весь путь целиком.

## 1. Backend (без изменений)

```bash
cd negotiator-backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # и заполнить SECRET_KEY
alembic upgrade head
python seed.py                  # демо-сценарии
python seed_cases.py            # 90 кейсов
python seed_admin.py            # тестовый админ
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Проверка: http://127.0.0.1:8000/api/v1/health/ → `{"status":"ok"}`.

Тестовый админ (создаётся `seed_admin.py`):
- Email: `admin@negotiator-ai.com`
- Пароль: `ChangeMeStrong123!`

Обычного пользователя проще всего завести прямо через фронтенд (форма
регистрации), либо через Swagger `/docs`.

## 2. Frontend (то, что было дополнено)

Распакуйте `negotiator-ai-frontend.zip` — это готовый Vite + React проект
(на репозиторий он не завязан, можно положить рядом с backend или
в `artifacts/negotiator-ai`, заменив прежнее содержимое).

```bash
cd ваш путь/negotiator-ai
npm install
npm approve-scripts --allow-scripts-pending
npm run dev
```

Откроется на **http://localhost:5173**. Всё, что фронт шлёт на `/api/...`,
dev-сервер Vite сам проксирует на `http://127.0.0.1:8000` (см.
`vite.config.js`) — благодаря этому же CORS в backend уже настроен по
умолчанию на `http://localhost:5173`, отдельно ничего донастраивать не
нужно.

Если backend крутится на другом хосте/порту — создайте `frontend/.env`
на основе `.env.example` и укажите там `VITE_API_URL`.

### Production-сборка

```bash
npm run build      # соберёт статику в frontend/dist
npm run preview    # локальный просмотр собранной версии
```

## 3. Что можно сделать в интерфейсе

- Зарегистрироваться (`/register`) → пройти онбординг → попасть в `/profile`.
- В `/catalog` — список опубликованных сценариев из backend, по категориям.
- `/constructor` → `/briefing` → `/session` — выбор кейса, брифинг без
  спойлеров и сам диалог с AI (текстовый чат через `POST /negotiation/message`).
- По завершении — `/analytics`: баллы, разбор реплик, рекомендации
  (`POST /negotiation/end` + `GET /negotiation/analysis/{id}`).
- Вход админа — `/login/admin` (или тестовый аккаунт выше) →
  `/admin/cases` — список своих кейсов, создание/редактирование
  (`/admin/cases/new`), публикация с получением ссылки-приглашения.

## 4. Что важно знать про эту версию фронтенда

- **Голос (STT/TTS) не подключён.** Backend поддерживает `POST
  /negotiation/voice`, но UI ведёт диалог текстом — это самая быстрая
  дорога до рабочего MVP. Голосовой ввод можно добавить позже отдельным
  компонентом на этом же эндпоинте (`MediaRecorder` → `FormData` →
  `negotiationApi.voice`, уже описан в `src/lib/api.js`).
- Все данные (каталог, сессии, аналитика, кейсы) реальные — идут из
  backend по контракту `API_CONTRACT.md`, никакого мока не осталось.
- Активная сессия переговоров временно хранится в `sessionStorage`
  (`negotiator-active-session` / `negotiator-last-session`) — это связывает
  страницы «Брифинг → Сессия → Аналитика» без глобального стора.
