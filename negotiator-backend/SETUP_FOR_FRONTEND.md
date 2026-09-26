# Как запустить NegotiatorAI backend

## Что нужно
- Python 3.12+ или Docker Desktop
- 30 минут времени

## Локально (без Docker)

1. Виртуальное окружение:
   python -m venv venv
   venv\Scripts\activate          # Windows
   source venv/bin/activate       # Mac/Linux

2. Зависимости:
   pip install -r requirements.txt

3. Скопировать .env:
   copy .env.example .env

4. Открыть .env и заполнить три поля:

   SECRET_KEY - сгенерировать командой:
     python -c "import secrets; print(secrets.token_urlsafe(32))"

   DASHSCOPE_API_KEY - ваш ключ Qwen.
     Получить: https://dashscope.console.aliyun.com/

   ADMIN_PASSWORD - минимум 12 символов. Придумайте сами.

   Без этих полей приложение не стартует.

5. Миграции:
   alembic upgrade head

6. Демо-данные:
   python seed.py           # 3 встроенных сценария
   python seed_cases.py     # 90 кейсов
   python seed_admin.py     # админ из .env

7. Запуск:
   uvicorn app.main:app --host 127.0.0.1 --port 8000

## Проверка

- http://127.0.0.1:8000/docs - Swagger UI
- http://127.0.0.1:8000/api/v1/health/ - должен вернуть
  {"status":"ok","database":"ok"}
- http://127.0.0.1:8000/openapi.json - схема для
  генерации TypeScript-типов

## Тестовые аккаунты

Админ создаётся из .env при запуске seed_admin.py:
- Email: ADMIN_EMAIL из .env
- Пароль: ADMIN_PASSWORD из .env

Обычного пользователя можно создать через Swagger:

POST /api/v1/auth/register
{
  "email": "test@example.com",
  "password": "Secret1234",
  "name": "Test",
  "consent_given": true
}

Затем ОБЯЗАТЕЛЬНО пройти онбординг:

POST /api/v1/auth/onboarding
{
  "directions": ["management", "clients"],
  "experience_level": "beginner"
}

Без онбординга /negotiation/start вернёт 403.

## CORS

Backend настроен на http://localhost:5173 (Vite по умолчанию).
Если фронт на другом порту - добавьте в .env:

  CORS_ORIGINS=http://localhost:5173,http://localhost:3000

И перезапустите backend.

## Генерация TypeScript-типов

npx openapi-typescript http://127.0.0.1:8000/openapi.json -o src/api-types.ts

## Особенности API

1. Формат ошибок HTTPException: { "detail": "..." }
   Формат ошибок валидации: { "error": "...", "details": [...] }
   Фронт должен обрабатывать оба.

2. /auth/me работает и для user, и для admin.

3. GET /scenarios/{id} возвращает БЕЗ спойлеров.
   Все поля - в /scenarios/{id}/admin (только для админа).

4. POST /negotiation/voice возвращает поле "reply",
   а не "reply_text".

5. POST /negotiation/end принимает session_id как
   query-параметр, а не body.

6. consent_given в /auth/register обязательный (422 без него).

7. Публичная регистрация админа ограничена:
   - 5 попыток в час с одного IP (429 при превышении)
   - может быть отключена через .env

## Известные ограничения

- TTS (озвучка ИИ) не реализован. ИИ отвечает текстом,
  пользователь говорит голосом.
- STT через faster-whisper, модель small (~500 МБ).
  Скачивается один раз при первом запуске сервера.
- Модель Whisper грузится при старте сервера (warmup).
  Первый запрос к /voice не должен тормозить.
- Сессии без активности >30 минут автоматически
  переводятся в interrupted фоновой задачей.