============================================================
NEGOTIATORAI - API CONTRACT
============================================================
Версия: 1.2
Дата:   26 сентября 2026
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

Ошибки валидации (422) от Pydantic:

  {
    "error": "Validation error",
    "details": [ { "loc": ["body","email"], "msg": "...", "type": "..." } ],
    "path": "http://127.0.0.1:8000/api/v1/..."
  }

Все остальные ошибки (400, 401, 403, 404, 410, 429, 500) от HTTPException:

  { "detail": "Описание ошибки" }

ВАЖНО: поля "error" в HTTPException-ответах нет.
Фронт должен читать err.response.data.detail.

Коды:
  200 - OK
  201 - Created
  204 - No Content
  400 - Bad Request
  401 - Unauthorized (нет токена)
  403 - Forbidden (не та роль или отключено)
  404 - Not Found
  410 - Gone (архивированный инвайт)
  422 - Validation Error
  429 - Too Many Requests (rate limit на регистрации админа)
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
  role=user  - работает только с user-эндпоинтами.
                /admin/* -> 403.
  role=admin - работает только с admin-эндпоинтами.
                /onboarding, /negotiation/*, /users/* -> 403.
                /auth/me - доступен ОБЕИМ ролям.

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
  password       обязательный, минимум 8 символов,
                 заглавная + строчная + цифра
  name           опциональный, до 100 символов
  consent_given  ОБЯЗАТЕЛЬНЫЙ. Если false -> 400.
                 Если не передан -> 422.

Response 201:
  { "access_token": "eyJ...", "token_type": "bearer" }

Ошибки:
  400 - дубликат email ИЛИ consent_given=false
  422 - валидация (в т.ч. отсутствие consent_given)


--- 3.2. POST /api/v1/auth/register/admin ---

Создать админа. Пропускает онбординг (status=active).

Гейты (все три проверяются по порядку):
  1. ADMIN_REGISTRATION_ENABLED в .env. Если false -> 403.
  2. ADMIN_REGISTRATION_CODE в .env. Если задан - обязателен
     в поле registration_code. Несовпадение -> 403.
  3. Rate limit: 5 регистраций в час с одного IP -> 429.

Request:
  {
    "email": "admin@negotiator-ai.com",
    "password": "AdminPass123",
    "name": "Administrator",
    "consent_given": true,
    "registration_code": null
  }

Поля:
  registration_code  опциональный. Требуется только если
                     ADMIN_REGISTRATION_CODE задан в .env.

Response 201: токен.

Ошибки:
  400 - дубликат email ИЛИ consent_given=false
  403 - регистрация отключена ИЛИ неверный код
  422 - валидация
  429 - слишком много попыток с одного IP


--- 3.3. POST /api/v1/auth/login ---

Request:  { "email": "...", "password": "..." }
Response 200: токен.
Ошибки: 401.


--- 3.4. POST /api/v1/auth/login/admin ---

Только для админов. Обычный user -> 403.

Request:  { "email": "...", "password": "..." }
Ошибки: 401 (неверный пароль), 403 (не админ).


--- 3.5. GET /api/v1/auth/me ---
          [ТРЕБУЕТ ТОКЕН, role=user ИЛИ admin]

Возвращает профиль текущего пользователя.
Работает и для админа - это мета-эндпоинт, не user-only.

Response 200:
  {
    "id": "uuid",
    "email": "user@example.com",
    "name": "Ivan",
    "avatar_url": null,
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

Поля:
  status: "pending_onboarding" | "active"
  rank_level: 1 | 2 | 3 | 4
  role: "user" | "admin"


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

Ошибки:
  400 - несуществующая категория
  403 - админ пытается пройти онбординг
  422 - слишком много направлений (больше 3)


============================================================
4. SCENARIOS
============================================================

--- 4.1. GET /api/v1/scenarios/ ---

Публичный каталог. Только встроенные сценарии
(admin_id = NULL AND status = 'ready').

Query: ?category=management
       (или ?category=scenario для legacy)

Response 200: массив кратких объектов.

Поля объекта:
  id, name, description, category, user_role, opponent_role

Спойлеры (opponent_goal, opponent_character, tactics,
concession_limits) НЕ возвращаются.


--- 4.2. GET /api/v1/scenarios/my ---
          [ТРЕБУЕТ ТОКЕН, role=admin]

Кейсы текущего админа (включая черновики).

Response 200: массив ScenarioAdminResponse.
Все поля, включая спойлеры, admin_id, status, invite_code.


--- 4.3. GET /api/v1/scenarios/{id} ---

Публичный предпросмотр одного сценария БЕЗ спойлеров.
Работает только для встроенных сценариев со статусом 'ready'.

Response 200:
  {
    "id": "scenario-1",
    "name": "Tough Buyer",
    "description": "...",
    "category": "clients",
    "user_role": "Seller",
    "opponent_role": "Buyer"
  }

НЕ возвращает:
  opponent_character, opponent_goal, opponent_interests,
  opponent_constraints, opponent_red_lines, tactics,
  concession_limits, initial_message

Ошибки:
  404 - сценарий не найден ИЛИ он admin-created ИЛИ
        статус не 'ready'


--- 4.4. GET /api/v1/scenarios/{id}/admin ---
          [ТРЕБУЕТ ТОКЕН, role=admin, только свой]

Админский вид своего сценария. Возвращает всё,
включая спойлеры.

Response 200: ScenarioAdminResponse (полный).

Ошибки:
  403 - сценарий принадлежит другому админу
  404 - сценарий не найден


--- 4.5. POST /api/v1/scenarios/ ---
          [ТРЕБУЕТ ТОКЕН, role=admin]

Создать черновик. Обязательное только "name".

Request:
  {
    "id": "my-case-1",
    "name": "Мой кейс",
    "description": "...",
    "category": "clients",
    "user_role": "Менеджер",
    "user_goal": "...",
    "opponent_role": "Клиент",
    "opponent_character": "...",
    "opponent_goal": "...",
    "opponent_interests": ["..."],
    "opponent_constraints": ["..."],
    "opponent_red_lines": ["..."],
    "concession_limits": {"price_min": 100},
    "tactics": ["anchor_low"],
    "communication_style": "Business-like",
    "tone_behavior": "Friendly",
    "non_standard_case": null,
    "initial_message": "..."
  }

Response 201: status="draft".

Ограничения длины:
  name                до 100
  description         до 5000
  category            до 50
  tone_behavior       до 2000
  non_standard_case   до 2000


--- 4.6. PUT /api/v1/scenarios/{id} ---
          [ТРЕБУЕТ ТОКЕН, admin, только свой]

Все поля опциональны. Обновляется только переданное.

Ограничения:
  Нельзя редактировать archived сценарий (400).
  Нельзя редактировать чужой сценарий (403).


--- 4.7. POST /api/v1/scenarios/{id}/publish ---
          [ТРЕБУЕТ ТОКЕН, admin, только свой]

Требует заполнения ВСЕХ обязательных полей:

Шаг 1 (FR-45):
  - category
  - name
  - description
  - opponent_role
  - user_goal
  - opponent_goal

Шаг 2 (FR-46):
  - tone_behavior
  - concession_limits

Response 200:
  {
    "id": "my-case-1",
    "status": "ready",
    "invite_code": "abc123XYZ",
    "invite_url": "/invite/abc123XYZ"
  }

Ошибки:
  400 - не заполнены обязательные поля
        (в detail перечислено, какие именно)
  403 - чужой сценарий
  404 - сценарий не найден


--- 4.8. POST /api/v1/scenarios/{id}/archive ---
          [ТРЕБУЕТ ТОКЕН, admin, только свой]

Response 200: { "id": "...", "status": "archived" }
Ссылка-приглашение перестаёт работать.


--- 4.9. DELETE /api/v1/scenarios/{id} ---
          [ТРЕБУЕТ ТОКЕН, admin, только свой]

Удаляет сценарий. У связанных сессий scenario_id = NULL.
Записи в user_added_cases удаляются.

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
  404 - код не найден ИЛИ сценарий в статусе draft
  410 - кейс архивирован ("This training is no longer active.")


--- 5.2. POST /api/v1/invite/{code} ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Принять инвайт (idempotent - повторный вызов вернёт
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
          [ТРЕБУЕТ ТОКЕН, role=user, onboarding_completed=true]

User со статусом pending_onboarding получит 403.

Request:
  {
    "scenario_id": "scenario-1",
    "difficulty": "practitioner",
    "relationship": "colleague",
    "power_balance": "equal"
  }

Поля (все опциональны кроме scenario_id):
  scenario_id       до 100 символов. Обязательный.
  difficulty        beginner | practitioner | expert
                    (по умолчанию из user.experience_level)
  relationship      stranger | colleague | friend | boss | subordinate
                    (по умолчанию из сценария)
  power_balance     user_strong | equal | opponent_strong

ВАЖНО: user_id НЕ передаётся. Берётся из токена.

Response 200:
  {
    "session_id": "uuid",
    "role": "Seller",
    "goal": "...",
    "opponent": "Buyer",
    "difficulty": "practitioner",
    "relationship": "colleague",
    "power_balance": "equal",
    "first_message": "..."
  }

Ошибки:
  403 - админ ИЛИ не пройден онбординг
  404 - сценарий не найден ИЛИ статус не 'ready'


--- 6.2. POST /api/v1/negotiation/message ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Request:
  {
    "session_id": "uuid",
    "message": "..."
  }

Поля:
  session_id   до 100 символов
  message      от 1 до 4000 символов

Response 200:
  { "reply": "...", "session_status": "ongoing" }

session_status: ongoing | finished | interrupted

Ошибки:
  400 - сессия finished или interrupted
  403 - чужая сессия
  404 - сессия не найдена
  422 - пустое сообщение или больше 4000 символов


--- 6.3. POST /api/v1/negotiation/voice ---
          [ТРЕБУЕТ ТОКЕН, role=user]

FormData:
  session_id: <uuid>
  audio: <файл .webm/.wav/.mp3/.ogg, до 10 МБ>
  language: <опционально, default "ru">

Response 200:
  {
    "user_text": "Hello...",
    "reply": "Let's discuss.",
    "session_status": "ongoing"
  }

ВАЖНО: поле называется "reply", не "reply_text".

Ошибки:
  400 - пустой файл, слишком большой, речь не распознана
  404 - сессия не найдена


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

ВНИМАНИЕ: session_id - query-параметр, не body!

Ошибки:
  400 - сессия interrupted ИЛИ нет ни одного сообщения от user
  404 - сессия не найдена
  500 - анализ упал после 3 retry

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

Idempotent: повторный вызов вернёт тот же отчёт,
новый анализ не запускается.


--- 6.6. GET /api/v1/negotiation/analysis/{session_id} ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Тот же ответ, что и /end.

Ошибки:
  404 - отчёта ещё нет ("No analysis found.")


--- 6.7. GET /api/v1/negotiation/sessions/{user_id} ---
          [ТРЕБУЕТ ТОКЕН, role=user]

Query: ?limit=50&offset=0

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

Ошибки:
  403 - чужой user_id


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

Сводка без спойлеров. Работает только для status='ready'.

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

Ошибки:
  404 - сценарий не найден ИЛИ статус не 'ready'


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

Метрики всегда возвращаются все три, даже если 0.


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
Если все пройдены - fallback (возвращает их же).


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

ВАЖНО: сессия становится interrupted либо явным вызовом
/interrupt, либо фоновым авто-таймаутом (нет активности
>30 минут по умолчанию).


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
   Body: { scenario_id }
   Сохранить session_id.

5. Диалог:
   POST /api/v1/negotiation/voice (FormData: session_id, audio)
   Ответ: { user_text, reply, session_status }

6. Завершение:
   POST /api/v1/negotiation/end?session_id={uuid}
   Показать scores, spin_analysis, batna_analysis,
   transcript_annotations (сопоставить с messages по index).

--- Admin flow ---

1. Регистрация админа:
   POST /api/v1/auth/register/admin
   Body: { email, password, name, consent_given: true }
   (опционально: registration_code, если включён в .env)

2. Создать кейс:
   POST /api/v1/scenarios/
   Body: { id, name, description, category, user_goal,
           opponent_role, opponent_goal,
           tone_behavior, concession_limits }

3. Опубликовать:
   POST /api/v1/scenarios/{id}/publish
   Получить invite_code и invite_url.

4. Раздать ссылку участникам.

5. Участник открывает ссылку:
   GET /api/v1/invite/{code} (публичный preview)
   POST /api/v1/invite/{code} (после логина, добавляет в
                               "Добавленные")


============================================================
10. ГЕНЕРАЦИЯ TYPESCRIPT-ТИПОВ
============================================================

npx openapi-typescript http://127.0.0.1:8000/openapi.json -o src/api-types.ts

============================================================
КОНЕЦ
============================================================