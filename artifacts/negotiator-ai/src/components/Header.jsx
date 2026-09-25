import { useState } from 'react';
import { Link } from 'wouter';
import { Menu, UserRound } from 'lucide-react';
import logo from "../assets/logo.png";

function Logo() {
  return (
    <Link href="/" className="brand" data-testid="link-logo">
      <img src={logo} alt="Fastur" className="brand-mark-img" />
    </Link>
  );
}

export default function Header({ user, onLogout }) {
  const [menu, setMenu] = useState(false);
  const firstName = user?.name?.split(' ')[0] || user?.email?.split('@')[0] || 'Профиль';

  return (
    <header className="topbar">
      <div className="container-wide topbar-inner">
        <Logo />
        <nav className="nav-links">
          <Link href="/catalog" data-testid="link-catalog">Тренировки</Link>
          {user?.role === 'user' && <Link href="/profile" data-testid="link-profile">Мой прогресс</Link>}
          {user?.role === 'admin' && <Link href="/admin/cases" data-testid="link-admin-cases">Мои кейсы</Link>}
          <a href="/#method" data-testid="link-method">Как это работает</a>
        </nav>
        <div className="top-actions">
          <button className="btn btn-quiet mobile-menu" onClick={() => setMenu(!menu)} aria-label="Открыть меню" data-testid="button-mobile-menu">
            <Menu size={18} />
          </button>
          {user ? (
            <>
              <Link href={user.role === 'admin' ? '/admin/cases' : '/profile'} className="btn btn-quiet btn-small" data-testid="link-account">
                <UserRound size={15} /> {firstName}
              </Link>
              <button onClick={onLogout} className="btn btn-small" data-testid="button-logout">Выйти</button>
            </>
          ) : (
            <>
              <Link href="/login" className="btn btn-quiet" data-testid="link-login">Войти</Link>
              <Link href="/register" className="btn btn-primary btn-small" data-testid="link-register">Начать</Link>
            </>
          )}
        </div>
        {menu && (
          <div className="card" style={{ position: 'absolute', right: 14, top: 58, padding: 12, display: 'grid', gap: 8, zIndex: 20 }}>
            <Link href="/catalog" className="btn btn-quiet btn-small" onClick={() => setMenu(false)}>Тренировки</Link>
            <a href="/#method" className="btn btn-quiet btn-small" onClick={() => setMenu(false)}>Как это работает</a>
          </div>
        )}
      </div>
    </header>
  );
}
