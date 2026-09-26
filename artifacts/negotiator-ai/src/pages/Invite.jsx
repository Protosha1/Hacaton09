// Приём ссылки-приглашения на кейс: GET /invite/{code} (публично) +
// POST /invite/{code} (после логина, добавляет кейс в "Добавленные").
import { useEffect, useState } from 'react';
import { Link, useLocation, useParams } from 'wouter';
import { ArrowRight } from 'lucide-react';
import { inviteApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import { categoryLabel } from '@/data/categories';

const PENDING_KEY = 'negotiator-pending-invite';

export default function Invite() {
  const { code } = useParams();
  const { user } = useAuth();
  const [, navigate] = useLocation();
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState('');
  const [accepting, setAccepting] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    inviteApi
      .preview(code)
      .then((data) => { if (!cancelled) setPreview(data); })
      .catch((err) => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [code]);

  // Гость должен сперва войти/зарегистрироваться — сохраняем код и
  // возвращаемся сюда же после входа, чтобы завершить приём приглашения.
  const goToLogin = (path) => {
    sessionStorage.setItem(PENDING_KEY, code);
    navigate(path);
  };

  // Если пользователь только что вошёл и у него есть отложенное приглашение
  // именно на этот код — примем его автоматически.
  useEffect(() => {
    if (!user || user.role !== 'user' || !preview) return;
    const pending = sessionStorage.getItem(PENDING_KEY);
    if (pending === code) {
      sessionStorage.removeItem(PENDING_KEY);
      accept();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, preview]);

  const accept = async () => {
    setAccepting(true);
    setError('');
    try {
      const res = await inviteApi.accept(code);
      navigate(`/constructor?case=${res.case_id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setAccepting(false);
    }
  };

  if (loading) return <p className="muted">Загружаем приглашение…</p>;

  if (error && !preview) {
    return (
      <div className="card" style={{ padding: 24, maxWidth: 520, margin: '40px auto' }}>
        <span className="eyebrow">Приглашение</span>
        <h2 style={{ margin: '10px 0' }}>Ссылка недействительна</h2>
        <p className="muted">{error}</p>
        <Link href="/catalog" className="btn btn-quiet" style={{ marginTop: 16 }}>В каталог</Link>
      </div>
    );
  }

  return (
    <div className="card briefing-card" style={{ maxWidth: 620 }}>
      <span className="eyebrow">Приглашение · {categoryLabel(preview.category)}</span>
      <h1 className="display" style={{ fontSize: 34, margin: '14px 0' }}>{preview.name}</h1>
      <p className="muted" style={{ lineHeight: 1.6 }}>{preview.description}</p>

      <div className="briefing-meta">
        <div className="meta-box"><small>ВАША РОЛЬ</small><strong>{preview.user_role || '—'}</strong></div>
        <div className="meta-box"><small>СОБЕСЕДНИК</small><strong>{preview.opponent_role || '—'}</strong></div>
      </div>

      {preview.user_goal && (
        <div className="card" style={{ padding: 20, background: 'rgba(17,14,37,.28)' }}>
          <span className="eyebrow">Цель</span>
          <p style={{ margin: '12px 0 0', lineHeight: 1.6 }}>{preview.user_goal}</p>
        </div>
      )}

      {error && <span className="form-error">{error}</span>}

      {!user && (
        <>
          <button className="btn btn-primary" style={{ width: '100%' }} onClick={() => goToLogin('/register')} data-testid="button-invite-register">
            Зарегистрироваться и открыть кейс <ArrowRight size={16} />
          </button>
          <button className="btn btn-quiet" style={{ width: '100%' }} onClick={() => goToLogin('/login')}>
            У меня уже есть аккаунт
          </button>
        </>
      )}

      {user && user.role === 'admin' && (
        <p className="muted">Приглашения принимают только пользовательские аккаунты. Войдите как участник, чтобы добавить этот кейс.</p>
      )}

      {user && user.role === 'user' && (
        <button className="btn btn-primary" style={{ width: '100%' }} disabled={accepting} onClick={accept} data-testid="button-invite-accept">
          {accepting ? 'Добавляем…' : <>Добавить кейс и начать <ArrowRight size={16} /></>}
        </button>
      )}
    </div>
  );
}
