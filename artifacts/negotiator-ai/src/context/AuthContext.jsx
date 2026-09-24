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
    } catch {
      // Токен протух или невалиден — тихо разлогиниваем.
      setToken(null);
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMe();
  }, [loadMe]);

  const login = async (email, password) => {
    const { access_token } = await authApi.login({ email, password });
    setToken(access_token);
    return loadMe();
  };

  const loginAdmin = async (email, password) => {
    const { access_token } = await authApi.loginAdmin({ email, password });
    setToken(access_token);
    const me = await loadMe();
    return { ...me, role: 'admin' };
  };

  const register = async (email, password, name) => {
    const { access_token } = await authApi.register({ email, password, name, consent_given: true });
    setToken(access_token);
    return loadMe();
  };

  const registerAdmin = async (email, password, name) => {
    const { access_token } = await authApi.registerAdmin({ email, password, name, consent_given: true });
    setToken(access_token);
    return loadMe();
  };

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
