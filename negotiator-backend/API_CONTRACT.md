# NegotiatorAI — API Contract

**Версия:** 1.0
**Дата:** 14 сентября 2026
**Base URL:** `http://127.0.0.1:8000`
**Интерактивная документация (Swagger):** `http://127.0.0.1:8000/docs`

Все запросы и ответы — JSON. Для загрузки аудио — `multipart/form-data`.

---

## Содержание

1. [Формат ошибок](#формат-ошибок)
2. [Аутентификация](#аутентификация)
3. [Auth — регистрация и профиль](#1-auth)
4. [Scenarios — сценарии](#2-scenarios)
5. [Negotiation — переговоры](#3-negotiation)
6. [History — история](#4-history)
7. [Progress — прогресс пользователя](#5-progress)
8. [Health — проверка](#6-health)
9. [Модели данных](#7-модели-данных)
10. [Типичные сценарии использования](#8-типичные-сценарии-использования)
11. [Обработка ошибок](#9-обработка-ошибок)
12. [CORS и безопасность](#10-cors-и-безопасность)

---

## Формат ошибок

Все ошибки возвращаются в едином формате:

```json
{
  "error": "Тип ошибки",
  "detail": "Описание ошибки"
}
```

**Ошибки валидации (422)** — от FastAPI/Pydantic:

```json
{
  "error": "Validation error",
  "details": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email",
      "input": "not-an-email"
    }
  ],
  "path": "http://127.0.0.1:8000/api/v1/auth/register"
}
```

**HTTP-коды:**

| Код | Значение |
|-----|----------|
| 200 | Успех |
| 201 | Создано (регистрация) |
| 400 | Bad Request (дубликат email, сессия уже завершена) |
| 401 | Unauthorized (нет токена / истёк) |
| 404 | Not Found (сценарий/сессия/пользователь) |
| 422 | Validation Error (неверный формат) |
| 500 | Internal Server Error |

---

## Аутентификация

**Схема:** JWT Bearer.

### Как получить токен

1. **Регистрация:** `POST /api/v1/auth/register` → получаете `access_token`.
2. Или **логин:** `POST /api/v1/auth/login` → получаете `access_token`.

### Как использовать

В каждом защищённом запросе добавляйте HTTP-заголовок:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

⚠️ **В Swagger UI** в поле Authorize вставляйте **только сам токен**, без слова `Bearer` — Swagger добавит его сам.

### Срок жизни токена

**7 дней** (`ACCESS_TOKEN_EXPIRE_MINUTES = 10080`). После истечения — 401, нужно залогиниться заново.

### Какой `sub` внутри токена

Внутри JWT — payload вида:
```json
{
  "sub": "user-uuid-здесь",
  "exp": 1727440000
}
```

`sub` = `user.id` из БД.

### Ключевая функция для фронта

```javascript
function getToken() {
  return localStorage.getItem("access_token");
}

function authHeaders() {
  const token = getToken();
  return token ? { "Authorization": `Bearer ${token}` } : {};
}
```

---

## 1. Auth

### 1.1. `POST /api/v1/auth/register`

Создать нового пользователя. Возвращает токен — сразу авторизован.

**Запрос:**
```json
{
  "email": "ivan@example.com",
  "password": "secret123",
  "name": "Ivan Petrov"
}
```

| Поле | Тип | Обязательное | Ограничения |
|------|-----|--------------|-------------|
| `email` | string | да | валидный email |
| `password` | string | да | min 6 символов |
| `name` | string | нет | до 100 символов |

**Ответ 201:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Ошибки:**
- `400` — email уже занят: `{"detail": "A user with this email already exists."}`
- `422` — неверный формат email / пароль короткий.

---

### 1.2. `POST /api/v1/auth/login`

**Запрос:**
```json
{
  "email": "ivan@example.com",
  "password": "secret123"
}
```

**Ответ 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Ошибки:**
- `401` — `{"detail": "Incorrect email or password."}`

---

### 1.3. `GET /api/v1/auth/me` 🔒

Требует токен.

**Ответ 200:**
```json
{
  "id": "a1b2c3d4-...",
  "email": "ivan@example.com",
  "name": "Ivan Petrov",
  "onboarding_completed": false,
  "directions": null,
  "experience_level": "beginner"
}
```

После онбординга:
```json
{
  "id": "a1b2c3d4-...",
  "email": "ivan@example.com",
  "name": "Ivan Petrov",
  "onboarding_completed": true,
  "directions": ["management", "clients"],
  "experience_level": "practitioner"
}
```

---

### 1.4. `POST /api/v1/auth/onboarding` 🔒

Сохранить результаты онбординга (FR-6, FR-7).

**Запрос:**
```json
{
  "directions": ["management", "clients"],
  "experience_level": "practitioner"
}
```

| Поле | Тип | Ограничения |
|------|-----|-------------|
| `directions` | array of strings | 1–3 значения из списка |
| `experience_level` | string | `beginner` \| `practitioner` \| `expert` |

**Допустимые значения `directions`:**

| Значение | Категория |
|----------|-----------|
| `management` | Общение с руководством |
| `hiring` | Собеседования и найм |
| `team` | Управление командой |
| `colleagues` | Взаимодействие с коллегами |
| `clients` | Обслуживание клиентов |
| `partners` | Переговоры с партнёрами |

**Ответ 200:**
```json
{
  "id": "a1b2c3d4-...",
  "email": "ivan@example.com",
  "name": "Ivan Petrov",
  "onboarding_completed": true,
  "directions": ["management", "clients"],
  "experience_level": "practitioner"
}
```

**Ошибки:**
- `400` — недопустимые значения `directions`.
- `422` — 4 категории / неверный уровень.

---

## 2. Scenarios

Сценарии — карточки кейсов. Всего **93**:
- 3 «legacy» demo (`scenario-1..3`).
- 90 кейсов (`case-1..90`) в 6 категориях по 15 штук.

### 2.1. `GET /api/v1/scenarios/`

Список всех сценариев. Опциональный фильтр по категории (FR-13).

**Query-параметры:**

| Параметр | Тип | Описание |
|----------|-----|----------|
| `category` | string | `management`, `hiring`, `team`, `colleagues`, `clients`, `partners`, или `scenario` (для legacy) |

**Примеры:**

```
GET /api/v1/scenarios/
GET /api/v1/scenarios/?category=management
GET /api/v1/scenarios/?category=scenario
```

**Ответ 200:**
```json
[
  {
    "id": "case-1",
    "name": "Обсуждение повышения",
    "description": "Обосновать готовность к повышению и обсудить новую роль",
    "user_role": "Employee",
    "opponent_role": "Manager"
  },
  ...
]
```

---

### 2.2. `GET /api/v1/scenarios/{scenario_id}`

Полная информация, включая «спойлеры» (цели оппонента, тактики).

**Ответ 200:**
```json
{
  "id": "case-1",
  "name": "Обсуждение повышения",
  "description": "Обосновать готовность к повышению и обсудить новую роль",
  "category": "management",
  "default_relationship": "subordinate",
  "default_power_balance": "opponent_strong",
  "user_role": "Employee",
  "user_goal": "Обосновать готовность к повышению и обсудить новую роль",
  "opponent_role": "Manager",
  "opponent_character": "Опытный руководитель...",
  "opponent_goal": "Руководитель предлагает сначала выполнить обязанности...",
  "opponent_interests": ["результат команды", "предсказуемость"],
  "opponent_constraints": ["ограничен бюджетом отдела"],
  "opponent_red_lines": ["ультиматумы", "обвинения без фактов"],
  "concession_limits": {"max_concessions": 3},
  "tactics": ["reference_to_team", "budget_constraints"],
  "communication_style": "Деловой, прямой, доброжелательный",
  "initial_message": "Привет! Давай сразу к делу — о чём хочешь поговорить?"
}
```

**Ошибки:**
- `404` — сценарий не найден.

---

## 3. Negotiation

### 3.1. `POST /api/v1/negotiation/start` 🔒

Начать новую сессию переговоров (FR-12).

**Запрос:**
```json
{
  "scenario_id": "case-1",
  "user_id": "user-1",
  "difficulty": "beginner",
  "relationship": "friend",
  "power_balance": "equal"
}
```

| Поле | Обязательное | Значения |
|------|--------------|----------|
| `scenario_id` | да | ID сценария |
| `user_id` | нет | ID пользователя (для истории) |
| `difficulty` | нет | `beginner` \| `practitioner` \| `expert`. Если не указано — берётся из `user.experience_level` |
| `relationship` | нет | `stranger` \| `colleague` \| `friend` \| `boss` \| `subordinate`. Если не указано — дефолт сценария |
| `power_balance` | нет | `user_strong` \| `equal` \| `opponent_strong`. Если не указано — дефолт сценария |

**Ответ 200:**
```json
{
  "session_id": "eee04178-9b53-4cf4-be39-a0b9663ec0ea",
  "role": "Employee",
  "goal": "Обосновать готовность к повышению и обсудить новую роль",
  "opponent": "Manager",
  "difficulty": "beginner",
  "relationship": "friend",
  "power_balance": "equal",
  "first_message": "Привет! Давай сразу к делу — о чём хочешь поговорить?"
}
```

**Ошибки:**
- `404` — сценарий не найден.
- `422` — неверные значения `difficulty`/`relationship`/`power_balance`.

---

### 3.2. `POST /api/v1/negotiation/message` 🔒

Отправить текстовое сообщение. ИИ отвечает с учётом контекста (FR-17).

**Запрос:**
```json
{
  "session_id": "eee04178-...",
  "message": "Здравствуйте, я хочу обсудить повышение."
}
```

**Ответ 200:**
```json
{
  "reply": "Отлично, давай обсудим. Что конкретно ты хочешь?",
  "session_status": "ongoing"
}
```

`session_status`: `ongoing` | `finished`.

**Ошибки:**
- `400` — `Session is already finished.`
- `404` — сессия не найдена.

---

### 3.3. `POST /api/v1/negotiation/voice` 🔒

Голосовое сообщение. Whisper распознаёт → LLM отвечает.

**Формат:** `multipart/form-data`

| Поле | Тип | Описание |
|------|-----|----------|
| `session_id` | string (form) | ID сессии |
| `audio` | file | Аудиофайл `.webm`, `.wav`, `.mp3`, `.ogg` |

**Пример на фронте (React):**

```javascript
const mediaRecorder = new MediaRecorder(stream);
const chunks = [];
mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
mediaRecorder.onstop = async () => {
  const blob = new Blob(chunks, { type: "audio/webm" });
  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("audio", blob, "voice.webm");

  const res = await fetch("http://127.0.0.1:8000/api/v1/negotiation/voice", {
    method: "POST",
    headers: authHeaders(),
    body: formData,
  });
  const data = await res.json();
  console.log("Вы сказали:", data.user_text);
  console.log("ИИ ответил:", data.reply_text);
};
```

**Ответ 200:**
```json
{
  "user_text": "Здравствуйте, я хочу обсудить повышение.",
  "reply_text": "Отлично, давай обсудим.",
  "session_status": "ongoing"
}
```

---

### 3.4. `POST /api/v1/negotiation/end?session_id={uuid}` 🔒

Завершить сессию и получить анализ (FR-19).

⚠️ **`session_id` — это query-параметр**, не body.

**Пример:**
```
POST /api/v1/negotiation/end?session_id=eee04178-9b53-4cf4-be39-a0b9663ec0ea
```

**Ответ 200:**
```json
{
  "session_id": "eee04178-...",
  "goal_achieved": "partial",
  "argumentation_score": 30,
  "objection_handling_score": 40,
  "overall_score": 42,
  "spin_score": 45,
  "batna_score": 20,
  "emotion_control_score": 85,
  "strengths": [
    "Чётко обозначили цель и сразу привели конкретный результат.",
    "Сохранили профессиональный и спокойный тон."
  ],
  "weaknesses": [
    "Аргументация поверхностная, без цифр.",
    "Не были согласованы условия пробного периода."
  ],
  "suggestions": [
    "Подготовьте количественные показатели.",
    "Используйте технику SPIN.",
    "Определите свою BATNA заранее."
  ],
  "full_report": "В ходе диалога вы чётко обозначили цель..."
}
```

**Ошибки:**
- `400` — нет сообщений в сессии.
- `404` — сессия не найдена.
- `500` — ошибка анализа (LLM недоступна).

---

### 3.5. `GET /api/v1/negotiation/analysis/{session_id}` 🔒

Получить сохранённый анализ (после `/end`).

**Ответ 200:** тот же, что и `/end`.

**Ошибки:**
- `404` — анализ не найден (сессия не завершена).

---

## 4. History

### 4.1. `GET /api/v1/negotiation/sessions/{user_id}` 🔒

Список всех сессий пользователя с оценками (FR-11).

⚠️ `user_id` — строка, типа `user-1`.

**Ответ 200:**
```json
[
  {
    "session_id": "eee04178-...",
    "scenario_id": "case-1",
    "scenario_name": "Обсуждение повышения",
    "role": "Employee",
    "goal": "Обосновать готовность...",
    "opponent": "Manager",
    "status": "finished",
    "created_at": "2026-09-13T23:31:29",
    "finished_at": "2026-09-13T23:34:18",
    "overall_score": 42
  }
]
```

Сортировка: **от новых к старым**.

---

### 4.2. `GET /api/v1/negotiation/sessions/{session_id}/messages` 🔒

Полная переписка (FR-21, FR-18).

**Ответ 200:**
```json
[
  {
    "sender": "ai",
    "text": "Привет! Давай сразу к делу — о чём хочешь поговорить?",
    "timestamp": "2026-09-13T23:31:29"
  },
  {
    "sender": "user",
    "text": "Здравствуйте, я хочу обсудить повышение.",
    "timestamp": "2026-09-13T23:32:11"
  }
]
```

`sender`: `user` | `ai`. Сортировка: **от старых к новым**.

---

## 5. Progress

### 5.1. `GET /api/v1/negotiation/progress/{user_id}` 🔒

Агрегированная статистика по всем завершённым сессиям (FR-10).

**Ответ 200:**
```json
{
  "total_sessions": 2,
  "finished_sessions": 2,
  "average_overall": 21.0,
  "average_argumentation": 15.0,
  "average_objection_handling": 20.0,
  "average_spin": 12.5,
  "average_batna": 10.0,
  "average_emotion_control": 42.5,
  "goal_achieved_count": 0
}
```

Если сессий нет — все значения `0.0` / `0`.

**Что показывает каждая метрика:**

| Метрика | Что оценивает |
|---------|---------------|
| `average_argumentation` | Качество аргументации |
| `average_objection_handling` | Работа с возражениями |
| `average_spin` | Использование SPIN-методики |
| `average_batna` | Осознание альтернатив |
| `average_emotion_control` | Контроль эмоций |
| `average_overall` | Общая оценка |

---

## 6. Health

### 6.1. `GET /api/v1/health/`

Проверка состояния сервиса.

**Ответ 200:**
```json
{
  "status": "ok",
  "database": "ok"
}
```

Если БД недоступна: `{"status": "degraded", "database": "unreachable"}`.

---

## 7. Модели данных

### User

```typescript
interface User {
  id: string;                    // UUID
  email: string;
  name: string | null;
  onboarding_completed: boolean;
  directions: string[] | null;   // ["management", "clients"]
  experience_level: "beginner" | "practitioner" | "expert";
}
```

### Scenario (кратко)

```typescript
interface ScenarioListItem {
  id: string;         // "case-1" или "scenario-1"
  name: string;
  description: string | null;
  user_role: string;
  opponent_role: string;
}
```

### ScenarioDetail (полно)

Добавляет:
```typescript
{
  category: string | null;
  default_relationship: string | null;
  default_power_balance: string | null;
  user_goal: string | null;
  opponent_character: string | null;
  opponent_goal: string | null;
  opponent_interests: string[];
  opponent_constraints: string[];
  opponent_red_lines: string[];
  concession_limits: object;
  tactics: string[];
  communication_style: string | null;
  initial_message: string | null;
}
```

### Session

```typescript
interface SessionListItem {
  session_id: string;
  scenario_id: string | null;
  scenario_name: string | null;
  role: string | null;
  goal: string | null;
  opponent: string | null;
  status: "ongoing" | "finished";
  created_at: string;            // ISO datetime
  finished_at: string | null;
  overall_score: number | null;
}
```

### Message

```typescript
interface Message {
  sender: "user" | "ai";
  text: string;
  timestamp: string;
}
```

### AnalysisReport

```typescript
interface AnalysisReport {
  session_id: string;
  goal_achieved: "yes" | "no" | "partial";
  argumentation_score: number;        // 0-100
  objection_handling_score: number;   // 0-100
  overall_score: number;              // 0-100
  spin_score: number | null;
  batna_score: number | null;
  emotion_control_score: number | null;
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
  full_report: string;
}
```

---

## 8. Типичные сценарии использования

### Полный flow новой тренировки

```javascript
// 1. Регистрация / логин
const { access_token } = await fetch("/api/v1/auth/register", {
  method: "POST",
  body: JSON.stringify({ email, password, name }),
}).then(r => r.json());
localStorage.setItem("access_token", access_token);

// 2. Онбординг (если onboarding_completed === false)
await fetch("/api/v1/auth/onboarding", {
  method: "POST",
  headers: { "Content-Type": "application/json", ...authHeaders() },
  body: JSON.stringify({
    directions: ["management", "clients"],
    experience_level: "practitioner",
  }),
});

// 3. Выбор категории → сценарии
const scenarios = await fetch("/api/v1/scenarios/?category=management", {
  headers: authHeaders(),
}).then(r => r.json());

// 4. Запуск сессии
const session = await fetch("/api/v1/negotiation/start", {
  method: "POST",
  headers: { "Content-Type": "application/json", ...authHeaders() },
  body: JSON.stringify({ scenario_id: "case-1", user_id: "user-1" }),
}).then(r => r.json());

// 5. Диалог (текст или голос)
const reply = await fetch("/api/v1/negotiation/message", {
  method: "POST",
  headers: { "Content-Type": "application/json", ...authHeaders() },
  body: JSON.stringify({ session_id: session.session_id, message: "..." }),
}).then(r => r.json());

// 6. Завершение
const analysis = await fetch(
  `/api/v1/negotiation/end?session_id=${session.session_id}`,
  { method: "POST", headers: authHeaders() }
).then(r => r.json());

// 7. После завершения:
//    - "Повторить" → снова /negotiation/start
//    - "Другой кейс" → /scenarios/...
//    - "В профиль" → /auth/me + /negotiation/progress/{user_id}
```

### Экран истории тренировок

```javascript
const sessions = await fetch(
  `/api/v1/negotiation/sessions/${userId}`,
  { headers: authHeaders() }
).then(r => r.json());

// Клик по сессии → детали
const messages = await fetch(
  `/api/v1/negotiation/sessions/${sessionId}/messages`,
  { headers: authHeaders() }
).then(r => r.json());

const analysis = await fetch(
  `/api/v1/negotiation/analysis/${sessionId}`,
  { headers: authHeaders() }
).then(r => r.json());
```

### Экран профиля — прогресс

```javascript
const progress = await fetch(
  `/api/v1/negotiation/progress/${userId}`,
  { headers: authHeaders() }
).then(r => r.json());

// progress.average_spin, progress.average_batna,
// progress.average_emotion_control → рисуем график
```

---

## 9. Обработка ошибок

### Пример универсальной обёртки

```javascript
async function apiCall(path, options = {}) {
  const res = await fetch(`http://127.0.0.1:8000${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...options.headers,
    },
  });

  if (res.status === 401) {
    localStorage.removeItem("access_token");
    window.location.href = "/login";
    return;
  }

  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || data.error || "Ошибка запроса");
  }

  return data;
}
```

### Что делать при каждой ошибке

| Код | Что делать на фронте |
|-----|----------------------|
| 400 | Показать `detail` пользователю |
| 401 | Очистить токен, редирект на логин |
| 404 | Показать «Не найдено», вернуться назад |
| 422 | Показать ошибку валидации (для форм) |
| 500 | «Сервис недоступен, попробуйте позже» |

---

## 10. CORS и безопасность

### CORS

Сейчас бэкенд разрешает запросы **с любых origin** (`allow_origins=["*"]`). Для продакшена — ограничить списком доменов фронта в `app/main.py`.

### Хранение токена

**Для MVP:** `localStorage` — просто, работает.

**Для прода:** `httpOnly cookies` — безопаснее (защита от XSS), но требует настройки CORS с `credentials: true`.

### Что НЕ надо делать

- ❌ Не хранить пароль в `localStorage`.
- ❌ Не отправлять токен в query-параметрах (утечёт в логи).
- ❌ Не логировать `Authorization` header.

---

## 11. Переменные окружения для фронта

Создайте `.env.local` в React-проекте:

```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Использование:

```javascript
const API = import.meta.env.VITE_API_BASE_URL;
```

При деплое на сервер — замените на реальный домен.

---

## 12. Roadmap и известные ограничения

### Что уже есть

- ✅ Аутентификация (email + JWT)
- ✅ Онбординг + профиль
- ✅ 93 сценария (6 категорий)
- ✅ Голосовой ввод (STT через Whisper)
- ✅ Авто-язык (RU/EN)
- ✅ Аналитика (SPIN, BATNA, эмоции)
- ✅ Прогресс пользователя
- ✅ История тренировок
- ✅ Docker для деплоя

### Чего нет (пока)

- ❌ **TTS** — озвучка ответов ИИ. Сейчас ИИ отвечает **текстом**, а пользователь говорит голосом.
- ❌ **Транскрипция с подсветкой** — не подсвечиваются неудачные фразы с альтернативами.
- ❌ **Рекомендации кейсов** — `GET /scenarios/recommended` не реализован.
- ❌ **Согласие на обработку данных** — нет поля `consent_given` при регистрации.
- ❌ **Флаг `interrupted`** — нет механизма «сессия прервана по потере сети».

Если фронтендеру нужны эти фичи — согласуйте со мной, добавим.

---

## 13. Контакты и поддержка

- **Swagger (живая документация):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **OpenAPI JSON (для генерации типов):** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)
- **README бэкенда:** [README.md](./README.md)

### Генерация TypeScript-типов

```bash
npx openapi-typescript http://127.0.0.1:8000/openapi.json -o src/api-types.ts
```

Все типы (`Scenario`, `Session`, `Message`, `AnalysisReport`) появятся автоматически в `src/api-types.ts`. Никаких ручных интерфейсов.