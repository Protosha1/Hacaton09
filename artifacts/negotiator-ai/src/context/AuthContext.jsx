// В context - ПРОВОДКА: данные, доступные всем страницам
// Хранит инфо: вошел ли пользователь, его имя опыт
function readStore(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}
 
function saveStore(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}
 
function AppContent() {
  const [user, setUser] = useState(() => readStore('negotiator-user', null));
  const setPersistedUser = value => { setUser(value); saveStore('negotiator-user', value); };
  const logout = () => { setUser(null); localStorage.removeItem('negotiator-user'); };
}
