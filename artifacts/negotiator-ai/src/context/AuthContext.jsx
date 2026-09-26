// Единый источник правды о текущем пользователе.
// Хранит JWT в localStorage и подтягивает профиль через GET /auth/me.
import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { authApi, setToken, getToken } from '@/lib/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadMe = useCallback(async () => {
    if (!getToken()) {
      setUser(null);
      setLoading(false);
      return null;
    }
    try {
      const me = await authApi.me();
      setUser(me);
      return me;
    } catch (err) {
      // Токен протух/невалиден (401) — тихо разлогиниваем.
      // Любая другая ошибка (сеть, 500) не должна выкидывать пользователя
      // из аккаунта: backend мог просто на секунду не ответить.
      if (err.status === 401) {
        setToken(null);
        setUser(null);
      }
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMe();
  }, [loadMe]);

  // Общий помощник для login/register: сохраняет токен, тянет профиль
  // и явно проверяет, что профиль правда загрузился — иначе бросает
  // ошибку вместо того, чтобы притвориться успешным входом.
  const authenticate = async (request) => {
    const { access_token } = await request();
    setToken(access_token);
    const me = await loadMe();
    if (!me) {
      setToken(null);
      throw new Error('Не удалось загрузить профиль после входа. Попробуйте ещё раз.');
    }
    return me;
  };

  const login = (email, password) => authenticate(() => authApi.login({ email, password }));

  const loginAdmin = (email, password) => authenticate(() => authApi.loginAdmin({ email, password }));

  const register = (email, password, name) =>
    authenticate(() => authApi.register({ email, password, name, consent_given: true }));

  const registerAdmin = (email, password, name) =>
    authenticate(() => authApi.registerAdmin({ email, password, name, consent_given: true }));

  const completeOnboarding = async (directions, experienceLevel) => {
    const updated = await authApi.onboarding({ directions, experience_level: experienceLevel });
    setUser(updated);
    return updated;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
  };

  const refresh = () => loadMe();

  return (
    <AuthContext.Provider
      value={{ user, loading, login, loginAdmin, register, registerAdmin, completeOnboarding, logout, refresh }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth должен использоваться внутри <AuthProvider>');
  return ctx;
}
