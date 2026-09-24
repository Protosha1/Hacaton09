// Единая форма для входа/регистрации — обычного пользователя и админа.
// Register.jsx, LoginAdmin.jsx и RegisterAdmin.jsx переиспользуют этот же компонент.
import { useState } from 'react';
import { Link, Redirect, useLocation } from 'wouter';
import { ArrowRight } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

export default function AuthPage({ mode, admin }) {
  const { user, login, loginAdmin, register, registerAdmin } = useAuth();
  const [, navigate] = useLocation();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Уже вошли — не показываем форму повторно.
  if (user) {
    return <Redirect to={user.role === 'admin' ? '/admin/cases' : user.status === 'pending_onboarding' ? '/onboarding' : '/profile'} />;
  }

  const submit = async (event) => {
    event.preventDefault();
    if (!email || !password || (mode === 'register' && admin && !name)) {
      setError('Заполните все обязательные поля');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      let result;
      if (mode === 'login') {
        result = admin ? await loginAdmin(email, password) : await login(email, password);
      } else {
        result = admin ? await registerAdmin(email, password, name) : await register(email, password, name);
      }
      if (admin) navigate('/admin/cases');
      else navigate(result?.status === 'active' ? '/profile' : '/onboarding');
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-wrap">
      <div className="card auth-card">
        <span className="eyebrow">{admin ? 'Рабочее пространство автора' : 'Личная арена'}</span>
        <h1 className="display">{mode === 'login' ? 'С возвращением.' : 'Начнём с вашего голоса.'}</h1>
        <p className="muted">
          {admin ? 'Создавайте кейсы для приглашённых команд.' : 'Регистрация нужна, чтобы сохранить ваш прогресс.'}
        </p>
        <form onSubmit={submit}>
          {(mode === 'register' || admin) && (
            <div className="field">
              <label htmlFor="name">Как вас зовут</label>
              <input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Имя и фамилия" autoComplete="name" data-testid="input-name" />
            </div>
          )}
          <div className="field">
            <label htmlFor="email">Почта</label>
            <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.ru" autoComplete="email" data-testid="input-email" />
          </div>
          <div className="field">
            <label htmlFor="password">Пароль</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Минимум 8 символов, заглавная буква и цифра"
              minLength={8}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              data-testid="input-password"
            />
          </div>
          {error && <span className="form-error">{error}</span>}
          <button className="btn btn-primary" type="submit" disabled={submitting} data-testid="button-submit-auth">
            {submitting ? 'Секунду…' : <>{mode === 'login' ? 'Войти в арену' : 'Создать профиль'} <ArrowRight size={16} /></>}
          </button>
        </form>
        <div className="form-footer">
          {admin ? (
            <>Не администратор? <Link href={mode === 'login' ? '/login' : '/register'}>{mode === 'login' ? 'Войти как пользователь' : 'Регистрация пользователя'}</Link></>
          ) : (
            <>{mode === 'login' ? 'Нет профиля? ' : 'Уже были здесь? '}<Link href={mode === 'login' ? '/register' : '/login'}>{mode === 'login' ? 'Создать его' : 'Войти'}</Link></>
          )}
        </div>
        <div style={{ textAlign: 'center', marginTop: 17 }}>
          <Link href={admin ? '/login' : '/login/admin'} className="muted" style={{ fontSize: 11 }}>
            {admin ? 'Перейти к пользовательскому входу' : 'Вход для администратора'}
          </Link>
        </div>
      </div>
    </div>
  );
}
