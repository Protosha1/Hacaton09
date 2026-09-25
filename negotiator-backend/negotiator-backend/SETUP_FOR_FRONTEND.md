# Как запустить NegotiatorAI backend (для фронтендера)

## Что нужно
- Python 3.12+ (или Docker Desktop)
- Git (если клонируешь)
- 20 минут времени


## локально (без Docker)

1. python -m venv venv
2. venv\Scripts\activate  (Windows)
   source venv/bin/activate  (Mac/Linux)
3. pip install -r requirements.txt
4. copy .env.example .env
5. Заполни SECRET_KEY (см. выше)
6. alembic upgrade head
7. python seed.py           # 3 демо-сценария
8. python seed_cases.py     # 90 кейсов
9. python seed_admin.py     # админ
10. uvicorn app.main:app --host 127.0.0.1 --port 8000

## Проверка

- http://127.0.0.1:8000/docs — Swagger
- http://127.0.0.1:8000/api/v1/health/ — должно вернуть {"status":"ok"}
- http://127.0.0.1:8000/openapi.json — OpenAPI-схема

## Тестовые аккаунты

После запуска seed_admin.py создаётся админ:
- Email: admin@negotiator-ai.com
- Пароль: ChangeMeStrong123!

Обычного пользователя можно зарегистрировать через Swagger:
POST /api/v1/auth/register
{
  "email": "test@example.com",
  "password": "Secret1234",
  "name": "Test",
  "consent_given": true
}

## CORS

Backend уже настроен на http://localhost:5173 — фронт Vite по умолчанию.
Если запускаешь фронт на другом порту — добавь в .env:
  CORS_ORIGINS=http://localhost:5173,http://localhost:3000

И перезапусти backend.

## Известные ограничения

- TTS (озвучка ИИ) не реализован. ИИ отвечает текстом, пользователь говорит голосом.
- STT работает через faster-whisper (локально, ~500 МБ модель)
- При первом запросе на /voice модель скачается — может занять 2–5 минут