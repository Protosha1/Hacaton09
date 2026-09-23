============================================================
NEGOTIATORAI — API CONTRACT
============================================================
Версия: 1.1
Дата:   22 сентября 2026
Base URL: http://127.0.0.1:8000
Swagger:  http://127.0.0.1:8000/docs
============================================================


============================================================
СОДЕРЖАНИЕ
============================================================
1.  Формат ошибок
2.  Аутентификация
3.  Auth
4.  Scenarios
5.  Invites
6.  Negotiation
7.  Users
8.  Health
9.  Типичные сценарии


============================================================
1. ФОРМАТ ОШИБОК
============================================================

Все ошибки:

  { "error": "Тип", "detail": "Описание" }

Ошибки валидации (422):

  {
    "error": "Validation error",
    "details": [ { "loc": ["body","email"], "msg": "...", "type": "..." } ],
    "path": "http://127.0.0.1:8000/api/v1/..."
  }

Коды:
  200 - OK
  201 - Created
  204 - No Content
  400 - Bad Request
  401 - Unauthorized (нет токена)
  403 - Forbidden (не та роль)
  404 - Not Found
  410 - Gone (архивированный инвайт)
  422 - Validation Error
  500 - Internal Error


============================================================
2. АУТЕНТИФИКАЦИЯ
============================================================

Схема: JWT Bearer. Токен живёт 7 дней.

Заголовок:
  Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

ВАЖНО: в Swagger UI вставляй только сам токен,
без слова "Bearer".

Правило ролей:
  role=user  — работает только с user-эндпоинтами.
                /admin/* → 403.
  role=admin — работает только с admin-эндпоинтами.
                /auth/me, /onboarding, /negotiation/*,
                /users/* → 403.

Token payload:
  { "sub": "user-uuid", "exp": 1727440000 }


============================================================
3. AUTH
============================================================

--- 3.1. POST /api/v1/auth/register ---

Создать обычного пользователя.

Request:
  {
    "email": "user@example.com",
    "password": "secret1234",
    "name": "Ivan Petrov",
    "consent_given": true
  }

Поля:
  email          обязательный, валидный email
  password       обязательный, минимум 8 символов
  name           опциональный, до 100 символов
  consent_given  bool. Если false — 400.

Response 201:
  { "access_token": "eyJ...", "token_type": "bearer" }

Ошибки:
  400 - дубликат email ИЛИ consent_given=false
  422 - валидация


--- 3.2. POST /api/v1/auth/register/admin ---

Создать админа. Пропускает онбординг (status=active).

Request:
  {
    "email": "admin@negotiator-ai.com",
    "password": "AdminPass123",
    "name": "Administrator",
    "consent_given": true
  }

Response 201: токен.


--- 3.3. POST /api/v1/auth/login ---

Request:  { "email": "...", "password": "..." }
Response 200: токен.
Ошибки: 401.


--- 3.4. POST /api/v1/auth/login/admin ---

Только для админов. Обычный user → 403.

Request:  { "email": "...", "password": "..." }
Ошибки: 401 (неверный пароль), 403 (не админ).


--- 3.5. GET /api/v1/auth/me ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Response 200:
  {
    "id": "uuid",
    "email": "user@example.com",
    "name": "Ivan",
    "role": "user",
    "status": "active",
    "onboarding_completed": true,
    "directions": ["management", "clients"],
    "experience_level": "practitioner",
    "total_xp": 250,
    "rank_level": 2,
    "rank_name": "Мастер тактики",
    "consent_given": true
  }

status: "pending_onboarding" | "active"
rank_level: 1 | 2 | 3 | 4


--- 3.6. POST /api/v1/auth/onboarding ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Request:
  {
    "directions": ["management", "clients"],
    "experience_level": "practitioner"
  }

directions: 1-3 значения из списка:
  management | hiring | team | colleagues | clients | partners
experience_level: beginner | practitioner | expert

Response 200: объект User, status теперь "active".


============================================================
4. SCENARIOS
============================================================

--- 4.1. GET /api/v1/scenarios/ ---

Публичный каталог. Только встроенные сценарии
(admin_id = NULL AND status = 'ready').

Query: ?category=management
       (или ?category=scenario для legacy)

Response 200: массив кратких объектов.

--- 4.2. GET /api/v1/scenarios/my ---
          [ТРЕБУЕТ ТОКЕН, role=admin]

Кейсы текущего админа (включая черновики).

Response 200: массив ScenarioAdminResponse.

--- 4.3. GET /api/v1/scenarios/{id} ---

Полная информация (со спойлерами —
opponent_character, opponent_goal, tactics, concession_limits).

--- 4.4. POST /api/v1/scenarios/ ---
          [ТРЕБУЕТ ТОКЕН, role=admin]

Создать черновик. Обязательное только "name".

Request:
  {
    "id": "my-case-1",
    "name": "Мой кейс",
    "category": "clients",
    "opponent_role": "Клиент",
    "opponent_character": "...",
    "user_goal": "...",
    "opponent_goal": "...",
    "concession_limits": {"price_min": 100},
    "tone_behavior": "Friendly",
    "non_standard_case": null,
    "initial_message": "..."
  }

Response 201: status="draft".

--- 4.5. PUT /api/v1/scenarios/{id} ---
          [ТРЕБУЕТ ТОКЕН, admin, только свой]

Все поля опциональны. Обновляется только переданное.

--- 4.6. POST /api/v1/scenarios/{id}/publish ---
          [ТРЕБУЕТ ТОКЕН, admin, только свой]

Требует tone_behavior и concession_limits.

Response 200:
  {
    "id": "my-case-1",
    "status": "ready",
    "invite_code": "abc123XYZ",
    "invite_url": "/invite/abc123XYZ"
  }

--- 4.7. POST /api/v1/scenarios/{id}/archive ---
          [ТРЕБУЕТ ТОКЕН, admin, только свой]

Response 200: { "id": "...", "status": "archived" }

--- 4.8. DELETE /api/v1/scenarios/{id} ---
          [ТРЕБУЕТ ТОКЕН, admin, только свой]

Удаляет. У связанных сессий scenario_id = NULL.

Response 204: пусто.


============================================================
5. INVITES
============================================================

--- 5.1. GET /api/v1/invite/{code} ---
          [ПУБЛИЧНЫЙ, без токена]

Preview инвайта.

Response 200:
  {
    "code": "abc123XYZ",
    "case_id": "my-case-1",
    "name": "...",
    "description": "...",
    "category": "clients",
    "user_role": "Sales",
    "opponent_role": "Client",
    "user_goal": "..."
  }

Ошибки:
  404 - код не найден
  410 - кейс архивирован ("Больше не активна")

--- 5.2. POST /api/v1/invite/{code} ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Принять инвайт (idempotent — повторный вызов вернёт
already_added=true).

Response 200:
  {
    "case_id": "my-case-1",
    "name": "...",
    "description": "...",
    "category": "clients",
    "user_role": "Sales",
    "opponent_role": "Client",
    "user_goal": "...",
    "already_added": false
  }


============================================================
6. NEGOTIATION
============================================================

--- 6.1. POST /api/v1/negotiation/start ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Request:
  {
    "scenario_id": "case-1",
    "user_id": "user-1",
    "difficulty": "practitioner",
    "relationship": "colleague",
    "power_balance": "equal"
  }

difficulty:       beginner | practitioner | expert
                  (по умолчанию из user.experience_level)
relationship:     stranger | colleague | friend | boss | subordinate
                  (по умолчанию из сценария)
power_balance:    user_strong | equal | opponent_strong

Response 200:
  {
    "session_id": "uuid",
    "role": "Employee",
    "goal": "...",
    "opponent": "Manager",
    "difficulty": "practitioner",
    "relationship": "colleague",
    "power_balance": "equal",
    "first_message": "..."
  }

--- 6.2. POST /api/v1/negotiation/message ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Request:  { "session_id": "uuid", "message": "..." }
Response: { "reply": "...", "session_status": "ongoing" }

session_status: ongoing | finished | interrupted

--- 6.3. POST /api/v1/negotiation/voice ---
          [ТРЕБУЕТ ТОКЕН, role=user]

FormData:
  session_id: <uuid>
  audio: <файл .webm/.wav/.mp3/.ogg>

Response 200:
  {
    "user_text": "Hello...",
    "reply_text": "Let's discuss.",
    "session_status": "ongoing"
  }

--- 6.4. POST /api/v1/negotiation/{id}/interrupt ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Idempotent. Ошибки: 400 (уже finished), 404.

Response 200:
  {
    "session_id": "...",
    "status": "interrupted",
    "finished_at": "..."
  }

--- 6.5. POST /api/v1/negotiation/end?session_id={uuid} ---
          [ТРЕБУЕТ ТОКЕН, role=user]

ВНИМАНИЕ: session_id — query-параметр, не body!

Response 200:
  {
    "session_id": "...",
    "goal_achieved": "partial",
    "argumentation_score": 60,
    "objection_handling_score": 55,
    "overall_score": 58,
    "spin_score": 45,
    "batna_score": 30,
    "emotion_control_score": 70,
    "spin_analysis": "...",
    "batna_analysis": "...",
    "transcript_annotations": [
      {
        "index": 0,
        "original": "...",
        "type": "strong" | "neutral" | "weak",
        "category": "opening" | "question" | "argument" |
                    "concession" | "objection_handling" |
                    "emotional" | "directive" | "other",
        "why": "...",
        "suggestion": null
      }
    ],
    "strong_count": 1,
    "weak_count": 1,
    "neutral_count": 0,
    "xp_earned": 60,
    "is_perfect": false,
    "strengths": [...],
    "weaknesses": [...],
    "suggestions": [...],
    "full_report": "..."
  }

Ошибки: 400 (interrupted / нет сообщений), 404, 500.

--- 6.6. GET /api/v1/negotiation/analysis/{session_id} ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Тот же ответ, что и /end.

--- 6.7. GET /api/v1/negotiation/sessions/{user_id} ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Response 200: массив сессий (от новых к старым):
  {
    "session_id": "...",
    "scenario_id": "case-1",
    "scenario_name": "Обсуждение повышения",
    "role": "Employee",
    "goal": "...",
    "opponent": "Manager",
    "status": "finished",
    "created_at": "...",
    "finished_at": "...",
    "overall_score": 58
  }

--- 6.8. GET /api/v1/negotiation/sessions/{id}/messages ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Response 200:
  [
    { "sender": "ai", "text": "...", "timestamp": "..." },
    { "sender": "user", "text": "...", "timestamp": "..." }
  ]

sender: user | ai

--- 6.9. GET /api/v1/negotiation/progress/{user_id} ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Response 200:
  {
    "total_sessions": 2,
    "finished_sessions": 2,
    "average_overall": 58.0,
    "average_argumentation": 60.0,
    "average_objection_handling": 55.0,
    "average_spin": 45.0,
    "average_batna": 30.0,
    "average_emotion_control": 70.0,
    "goal_achieved_count": 0
  }

--- 6.10. GET /api/v1/negotiation/briefing/{scenario_id} ---
           [ТРЕБУЕТ ТОКЕН, role=user]

Сводка без спойлеров.

Response 200:
  {
    "scenario_id": "case-1",
    "name": "Обсуждение повышения",
    "description": "...",
    "category": "management",
    "user_role": "Employee",
    "user_goal": "...",
    "opponent_role": "Manager",
    "initial_message": "..."
  }


============================================================
7. USERS
============================================================

--- 7.1. GET /api/v1/users/{user_id}/skills ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Response 200:
  {
    "user_id": "user-1",
    "skills": [
      { "metric": "emotion_control",
        "current_value": 70,
        "sessions_count": 2,
        "history": [80, 60],
        "updated_at": "..." },
      { "metric": "batna", "current_value": 30, ... },
      { "metric": "spin",  "current_value": 45, ... }
    ]
  }

--- 7.2. GET /api/v1/users/{user_id}/recommendations ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Query: ?limit=10

Response 200:
  {
    "user_id": "user-1",
    "total": 5,
    "recommendations": [
      {
        "case_id": "case-1",
        "name": "...",
        "description": "...",
        "category": "management",
        "user_role": "Employee",
        "opponent_role": "Manager"
      }
    ]
  }

Логика: из directions, исключая пройденные.
Если все пройдены — fallback (возвращает их же).

--- 7.3. GET /api/v1/users/{user_id}/interrupted-session ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Всегда 200.

Response 200 (есть):
  {
    "has_interrupted": true,
    "session": {
      "session_id": "...",
      "scenario_id": "case-1",
      "scenario_name": "...",
      "role": "Employee",
      "goal": "...",
      "difficulty": "practitioner",
      "relationship": "colleague",
      "power_balance": "equal",
      "created_at": "...",
      "finished_at": "...",
      "messages_count": 3
    }
  }

Если нет: { "has_interrupted": false, "session": null }

--- 7.4. GET /api/v1/users/{user_id}/added-cases ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Response 200:
  {
    "user_id": "user-1",
    "total": 1,
    "cases": [
      {
        "case_id": "my-case-1",
        "name": "...",
        "description": "...",
        "category": "clients",
        "user_role": "Sales",
        "opponent_role": "Client",
        "added_at": "..."
      }
    ]
  }


============================================================
8. HEALTH
============================================================

GET /api/v1/health/   -> { "status": "ok", "database": "ok" }
GET /                -> { "message": "...", "version": "0.1.0" }


============================================================
9. ТИПИЧНЫЕ СЦЕНАРИИ
============================================================

--- Полный flow тренировки ---

1. Регистрация:
   POST /api/v1/auth/register
   Body: { email, password, name, consent_given: true }
   Сохранить access_token.

2. Онбординг:
   POST /api/v1/auth/onboarding
   Body: { directions: [...], experience_level: "..." }

3. Briefing:
   GET /api/v1/negotiation/briefing/{scenario_id}
   Показать name, goal, opponent_role. Проверить микрофон.

4. Старт:
   POST /api/v1/negotiation/start
   Body: { scenario_id, user_id }
   Сохранить session_id.

5. Диалог:
   POST /api/v1/negotiation/voice (FormData: session_id, audio)

6. Завершение:
   POST /api/v1/negotiation/end?session_id={uuid}
   Показать scores, spin_analysis, batna_analysis,
   transcript_annotations (сопоставить с messages по index).

--- Admin flow ---

1. Регистрация админа:
   POST /api/v1/auth/register/admin
   Body: { email, password, name, consent_given: true }

2. Создать кейс:
   POST /api/v1/scenarios/
   Body: { id, name, tone_behavior, concession_limits, ... }

3. Опубликовать:
   POST /api/v1/scenarios/{id}/publish
   Получить invite_code и invite_url.

4. Раздать ссылку пользователям.


============================================================
10. ГЕНЕРАЦИЯ TYPESCRIPT-ТИПОВ
============================================================

npx openapi-typescript http://127.0.0.1:8000/openapi.json -o src/api-types.ts

============================================================
КОНЕЦ
============================================================