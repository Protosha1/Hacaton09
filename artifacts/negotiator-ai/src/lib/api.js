// Единая точка входа для всех обращений к backend.
// Все пути соответствуют negotiator-backend/API_CONTRACT.md (v1.1).
import axios from 'axios';

const baseURL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : '/api/v1';

export const client = axios.create({ baseURL });

const TOKEN_KEY = 'negotiator-token';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

client.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Приводим ошибки backend { error, detail } / { error, details[] } к единому читаемому тексту.
function unwrap(promise) {
  return promise.catch((err) => {
    const data = err.response?.data;
    let message = 'Что-то пошло не так. Попробуйте ещё раз.';
    if (data?.detail) message = data.detail;
    else if (data?.details?.length) message = data.details.map((d) => d.msg).join('; ');
    else if (err.message === 'Network Error') message = 'Не удаётся связаться с сервером. Backend запущен?';
    const wrapped = new Error(message);
    wrapped.status = err.response?.status;
    throw wrapped;
  });
}

// ---- Auth ----
export const authApi = {
  register: (payload) => unwrap(client.post('/auth/register', payload)).then((r) => r.data),
  registerAdmin: (payload) => unwrap(client.post('/auth/register/admin', payload)).then((r) => r.data),
  login: (payload) => unwrap(client.post('/auth/login', payload)).then((r) => r.data),
  loginAdmin: (payload) => unwrap(client.post('/auth/login/admin', payload)).then((r) => r.data),
  me: () => unwrap(client.get('/auth/me')).then((r) => r.data),
  onboarding: (payload) => unwrap(client.post('/auth/onboarding', payload)).then((r) => r.data),
};

// ---- Scenarios ----
export const scenariosApi = {
  list: (category) => unwrap(client.get('/scenarios/', { params: category ? { category } : {} })).then((r) => r.data),
  mine: () => unwrap(client.get('/scenarios/my')).then((r) => r.data),
  get: (id) => unwrap(client.get(`/scenarios/${id}`)).then((r) => r.data),
  create: (payload) => unwrap(client.post('/scenarios/', payload)).then((r) => r.data),
  update: (id, payload) => unwrap(client.put(`/scenarios/${id}`, payload)).then((r) => r.data),
  publish: (id) => unwrap(client.post(`/scenarios/${id}/publish`)).then((r) => r.data),
  archive: (id) => unwrap(client.post(`/scenarios/${id}/archive`)).then((r) => r.data),
  remove: (id) => unwrap(client.delete(`/scenarios/${id}`)).then((r) => r.data),
};

// ---- Invites ----
export const inviteApi = {
  preview: (code) => unwrap(client.get(`/invite/${code}`)).then((r) => r.data),
  accept: (code) => unwrap(client.post(`/invite/${code}`)).then((r) => r.data),
};

// ---- Negotiation ----
export const negotiationApi = {
  start: (payload) => unwrap(client.post('/negotiation/start', payload)).then((r) => r.data),
  message: (payload) => unwrap(client.post('/negotiation/message', payload)).then((r) => r.data),
  voice: (formData) => unwrap(client.post('/negotiation/voice', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })).then((r) => r.data),
  interrupt: (sessionId) => unwrap(client.post(`/negotiation/${sessionId}/interrupt`)).then((r) => r.data),
  end: (sessionId) => unwrap(client.post(`/negotiation/end?session_id=${sessionId}`)).then((r) => r.data),
  analysis: (sessionId) => unwrap(client.get(`/negotiation/analysis/${sessionId}`)).then((r) => r.data),
  sessions: (userId) => unwrap(client.get(`/negotiation/sessions/${userId}`)).then((r) => r.data),
  sessionMessages: (sessionId) => unwrap(client.get(`/negotiation/sessions/${sessionId}/messages`)).then((r) => r.data),
  progress: (userId) => unwrap(client.get(`/negotiation/progress/${userId}`)).then((r) => r.data),
  briefing: (scenarioId) => unwrap(client.get(`/negotiation/briefing/${scenarioId}`)).then((r) => r.data),
};

// ---- Users ----
export const usersApi = {
  skills: (userId) => unwrap(client.get(`/users/${userId}/skills`)).then((r) => r.data),
  recommendations: (userId, limit = 10) => unwrap(client.get(`/users/${userId}/recommendations`, { params: { limit } })).then((r) => r.data),
  interruptedSession: (userId) => unwrap(client.get(`/users/${userId}/interrupted-session`)).then((r) => r.data),
  addedCases: (userId) => unwrap(client.get(`/users/${userId}/added-cases`)).then((r) => r.data),
};

// ---- Health ----
export const healthApi = {
  check: () => unwrap(client.get('/health/')).then((r) => r.data),
};
