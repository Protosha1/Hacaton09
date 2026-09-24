// Экран симуляции: текстовый диалог с AI-собеседником.
import { useEffect, useRef, useState } from 'react';
import { Redirect, useLocation } from 'wouter';
import { Send, User, Bot, X } from 'lucide-react';
import { negotiationApi } from '@/lib/api';

function loadActiveSession() {
  try {
    const raw = sessionStorage.getItem('negotiator-active-session');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export default function Session() {
  const [, navigate] = useLocation();
  const [session] = useState(loadActiveSession);
  const [messages, setMessages] = useState(() => (session ? [{ sender: 'ai', text: session.first_message }] : []));
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [error, setError] = useState('');
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  if (!session) return <Redirect to="/catalog" />;

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;
    setInput('');
    setMessages((prev) => [...prev, { sender: 'user', text }]);
    setSending(true);
    setError('');
    try {
      const res = await negotiationApi.message({ session_id: session.session_id, message: text });
      setMessages((prev) => [...prev, { sender: 'ai', text: res.reply }]);
      if (res.session_status === 'finished') {
        await finish(true);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSending(false);
    }
  };

  const finish = async (alreadyFinished = false) => {
    setFinishing(true);
    try {
      if (!alreadyFinished) await negotiationApi.end(session.session_id);
      else await negotiationApi.analysis(session.session_id).catch(() => negotiationApi.end(session.session_id));
      sessionStorage.setItem('negotiator-last-session', session.session_id);
      sessionStorage.removeItem('negotiator-active-session');
      navigate('/analytics');
    } catch (err) {
      setError(err.message);
      setFinishing(false);
    }
  };

  return (
    <div className="session-page">
      <div className="session-wrap" style={{ maxWidth: 720, width: '100%' }}>
        <span className="eyebrow">{session.scenario_name || 'Переговоры'} · вы играете роль «{session.role}»</span>
        <h1 className="display" style={{ fontSize: 28, margin: '10px 0' }}>{session.goal}</h1>
        <p className="muted" style={{ marginBottom: 16 }}>Собеседник: {session.opponent}</p>

        <div
          ref={scrollRef}
          className="card"
          style={{ maxHeight: 420, overflowY: 'auto', padding: 18, display: 'flex', flexDirection: 'column', gap: 12 }}
        >
          {messages.map((m, i) => (
            <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', flexDirection: m.sender === 'user' ? 'row-reverse' : 'row' }}>
              <span style={{ opacity: 0.7, flexShrink: 0, marginTop: 2 }}>{m.sender === 'user' ? <User size={16} /> : <Bot size={16} />}</span>
              <div
                className={m.sender === 'user' ? 'card-lavender' : ''}
                style={{
                  padding: '10px 14px',
                  borderRadius: 14,
                  background: m.sender === 'user' ? undefined : 'rgba(17,14,37,.35)',
                  maxWidth: '80%',
                  lineHeight: 1.5,
                  fontSize: 14,
                }}
              >
                {m.text}
              </div>
            </div>
          ))}
          {sending && <p className="muted" style={{ fontSize: 12 }}>Собеседник печатает…</p>}
        </div>

        {error && <span className="form-error">{error}</span>}

        <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
            placeholder="Напишите свою реплику…"
            disabled={sending || finishing}
            data-testid="input-message"
            style={{ flex: 1 }}
          />
          <button className="btn btn-primary" onClick={send} disabled={sending || finishing || !input.trim()} data-testid="button-send-message">
            <Send size={16} />
          </button>
        </div>

        <button className="btn btn-quiet" style={{ marginTop: 16 }} onClick={() => setConfirm(true)} data-testid="button-end-session">
          Завершить разговор <X size={15} />
        </button>
        <p className="muted" style={{ fontSize: 11, marginTop: 12 }}>Не нужно быть идеальным. Просто продолжайте.</p>
      </div>

      {confirm && (
        <div style={{ position: 'fixed', inset: 0, zIndex: 30, display: 'grid', placeItems: 'center', background: 'rgba(8,5,22,.72)', padding: 20 }}>
          <div className="card" style={{ width: 'min(420px,100%)', padding: 27 }}>
            <span className="eyebrow">Пауза</span>
            <h2 className="display" style={{ fontSize: 29, margin: '13px 0' }}>Завершить разговор?</h2>
            <p className="muted" style={{ fontSize: 13, lineHeight: 1.6 }}>Мы сохраним эту попытку и покажем разбор сильных и слабых мест.</p>
            <div style={{ display: 'flex', gap: 9, marginTop: 24 }}>
              <button className="btn btn-quiet" onClick={() => setConfirm(false)} style={{ flex: 1 }}>Продолжить</button>
              <button className="btn btn-primary" onClick={() => finish(false)} disabled={finishing} style={{ flex: 1 }} data-testid="button-confirm-end">
                {finishing ? 'Завершаем…' : 'Завершить'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
