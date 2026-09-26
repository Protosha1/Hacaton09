// Экран симуляции: пользователь говорит голосом, AI-собеседник отвечает текстом.
import { useEffect, useRef, useState } from 'react';
import { Redirect, useLocation } from 'wouter';
import { Mic, Square, User, Bot, X, Loader2 } from 'lucide-react';
import { negotiationApi, getToken } from '@/lib/api';

// Подбираем поддерживаемый браузером формат записи (Safari/Chrome отличаются).
function pickMimeType() {
  const candidates = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg'];
  for (const type of candidates) {
    if (window.MediaRecorder?.isTypeSupported?.(type)) return type;
  }
  return '';
}

function loadActiveSession() {
  try {
    const raw = sessionStorage.getItem('negotiator-active-session');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

// Ключ для сохранения истории реплик конкретной сессии — переживает
// перезагрузку страницы (backend не умеет отдавать историю "на лету",
// а сообщения sessions/{id}/messages появляются там только после ответа AI,
// так что храним свою копию локально, привязанную к session_id).
function transcriptKey(sessionId) {
  return `negotiator-transcript-${sessionId}`;
}

function loadTranscript(sessionId, fallbackFirstMessage) {
  try {
    const raw = sessionStorage.getItem(transcriptKey(sessionId));
    if (raw) return JSON.parse(raw);
  } catch {
    /* ignore corrupted cache */
  }
  return fallbackFirstMessage ? [{ sender: 'ai', text: fallbackFirstMessage }] : [];
}

export default function Session() {
  const [, navigate] = useLocation();
  const [session] = useState(loadActiveSession);
  const [messages, setMessages] = useState(() => (session ? loadTranscript(session.session_id, session.first_message) : []));
  const [sending, setSending] = useState(false);
  const [recording, setRecording] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [finishing, setFinishing] = useState(false);
  const [error, setError] = useState('');
  const scrollRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const streamRef = useRef(null);
  const finishedRef = useRef(false);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  // Каждое изменение переписываем в sessionStorage, чтобы при случайной
  // перезагрузке страницы разговор не пропадал.
  useEffect(() => {
    if (!session) return;
    sessionStorage.setItem(transcriptKey(session.session_id), JSON.stringify(messages));
  }, [messages, session]);

  useEffect(() => () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
  }, []);

  // Если пользователь уходит со страницы (закрывает вкладку, обновляет,
  // жмёт "назад") посреди незавершённого разговора — явно помечаем сессию
  // прерванной на backend, а не оставляем её висеть в "ongoing" навсегда.
  useEffect(() => {
    if (!session) return undefined;
    const markInterrupted = () => {
      if (finishedRef.current) return;
      const token = getToken();
      if (!token) return;
      const base = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api/v1` : '/api/v1';
      // sendBeacon здесь не подходит: он не умеет передавать заголовок
      // Authorization, а без него backend ответит 401. fetch с keepalive
      // поддерживает заголовки и переживает уход со страницы в браузерах
      // на основе Chromium/Firefox.
      fetch(`${base}/negotiation/${session.session_id}/interrupt`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        keepalive: true,
      }).catch(() => {});
    };
    window.addEventListener('beforeunload', markInterrupted);
    return () => {
      window.removeEventListener('beforeunload', markInterrupted);
      // Уход на другую страницу этого приложения (без перезагрузки) —
      // тоже прерывание разговора, если он не был явно завершён.
      markInterrupted();
    };
  }, [session]);

  if (!session) return <Redirect to="/catalog" />;

  const hasUserMessage = messages.some((m) => m.sender === 'user');

  const startRecording = async () => {
    if (recording || sending || finishing) return;
    setError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mimeType = pickMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      chunksRef.current = [];
      recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: mimeType || 'audio/webm' });
        sendVoice(blob);
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch (err) {
      setError('Не удалось получить доступ к микрофону. Разрешите доступ и попробуйте снова.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  };

  const sendVoice = async (blob) => {
    if (blob.size < 1000) {
      setError('Запись слишком короткая. Удержите кнопку и скажите фразу.');
      return;
    }
    setSending(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('session_id', session.session_id);
      formData.append('audio', blob, 'voice.webm');
      const res = await negotiationApi.voice(formData);
      setMessages((prev) => [
        ...prev,
        { sender: 'user', text: res.user_text || '(не удалось распознать речь)' },
        { sender: 'ai', text: res.reply },
      ]);
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
      finishedRef.current = true;
      sessionStorage.setItem('negotiator-last-session', session.session_id);
      sessionStorage.removeItem('negotiator-active-session');
      sessionStorage.removeItem(transcriptKey(session.session_id));
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
          {sending && <p className="muted" style={{ fontSize: 12 }}><Loader2 size={12} className="spin" style={{ verticalAlign: '-2px', marginRight: 6 }} />Собеседник печатает…</p>}
        </div>

        {error && <span className="form-error">{error}</span>}

        <div className="voice-control-wrap">
          <button
            className={`btn btn-primary mic-button${recording ? ' mic-button-active' : ''}`}
            onClick={recording ? stopRecording : startRecording}
            disabled={sending || finishing}
            data-testid="button-voice-record"
          >
            {recording ? <Square size={18} /> : <Mic size={18} />}
          </button>
          <p className="muted" style={{ fontSize: 12, margin: '10px 0 0' }}>
            {recording ? 'Идёт запись… нажмите ещё раз, чтобы отправить' : sending ? 'Распознаём и отправляем реплику…' : 'Нажмите и скажите свою реплику вслух'}
          </p>
        </div>

        <button
          className="btn btn-quiet"
          style={{ marginTop: 16 }}
          onClick={() => setConfirm(true)}
          disabled={!hasUserMessage || sending}
          title={hasUserMessage ? undefined : 'Скажите хотя бы одну реплику, прежде чем завершать'}
          data-testid="button-end-session"
        >
          Завершить разговор <X size={15} />
        </button>
        {!hasUserMessage && (
          <p className="muted" style={{ fontSize: 11, marginTop: 8 }}>
            Разбор станет доступен после первой вашей реплики.
          </p>
        )}
        <p className="muted" style={{ fontSize: 11, marginTop: 12 }}>Не нужно быть идеальным. Просто продолжайте — говорите, а Fastur ответит текстом.</p>
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
