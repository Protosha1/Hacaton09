// Экран итогов: разбор диалога, баллы и рекомендации.
import { useEffect, useState } from 'react';
import { Redirect, useLocation } from 'wouter';
import { ArrowRight, Copy, RotateCcw } from 'lucide-react';
import { negotiationApi } from '@/lib/api';

const goalLabels = { yes: 'Успех', partial: 'Частично', no: 'Не достигнута' };

export default function Analytics({ onToast }) {
  const [, navigate] = useLocation();
  const sessionId = sessionStorage.getItem('negotiator-last-session');
  const [data, setData] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!sessionId) return;
    negotiationApi.analysis(sessionId).then(setData).catch((err) => setError(err.message));
  }, [sessionId]);

  if (!sessionId) return <Redirect to="/profile" />;
  if (error) return <div className="card" style={{ padding: 24 }}><p className="muted">{error}</p></div>;
  if (!data) return <p className="muted">Считаем результаты…</p>;

  const copyTranscript = () => {
    const text = data.transcript_annotations.map((a) => a.original).join('\n');
    navigator.clipboard?.writeText(text);
    onToast?.('Транскрипт скопирован');
  };

  return (
    <>
      <div className="page-header">
        <div>
          <span className="eyebrow">Разбор завершён</span>
          <h1 className="display">{goalLabels[data.goal_achieved] || data.goal_achieved}</h1>
          <p className="muted">Ниже — то, что уже работает, и точки роста для следующей попытки.</p>
        </div>
        <span className="tag">+{data.xp_earned} XP начислено</span>
      </div>

      <div className="analytics-grid">
        <div className="card verdict-card">
          <span className="eyebrow">Вердикт AI</span>
          <div className="verdict-big">{goalLabels[data.goal_achieved] || data.goal_achieved}</div>
          <p className="soft">{data.full_report}</p>
          <div className="stat-strip">
            <div className="stat"><span className="muted" style={{ fontSize: 11 }}>Итог</span><strong>{data.overall_score}</strong></div>
            <div className="stat"><span className="muted" style={{ fontSize: 11 }}>SPIN</span><strong>{data.spin_score ?? '—'}</strong></div>
            <div className="stat"><span className="muted" style={{ fontSize: 11 }}>BATNA</span><strong>{data.batna_score ?? '—'}</strong></div>
            <div className="stat"><span className="muted" style={{ fontSize: 11 }}>Эмоции</span><strong>{data.emotion_control_score ?? '—'}</strong></div>
          </div>
        </div>

        <div className="card transcript">
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <div>
              <span className="eyebrow">Транскрипт</span>
              <h2 style={{ margin: '9px 0 0', fontSize: 21 }}>Фрагменты разговора</h2>
            </div>
            <button className="btn btn-quiet btn-small" onClick={copyTranscript} data-testid="button-copy-transcript">
              <Copy size={14} /> Копировать
            </button>
          </div>
          {data.transcript_annotations.length === 0 && <p className="muted">Нет размеченных реплик.</p>}
          {data.transcript_annotations.map((a) => (
            <div className="transcript-line" key={a.index}>
              <span className="muted">Вы:</span> <span className={a.type === 'weak' ? 'weak' : undefined}>{a.original}</span>
              {a.suggestion && <div className="alternative">→ {a.suggestion}</div>}
              {!a.suggestion && a.why && <div className="alternative">{a.why}</div>}
            </div>
          ))}
        </div>

        {(data.spin_analysis || data.batna_analysis) && (
          <div className="card" style={{ padding: 24, gridColumn: '1 / -1' }}>
            <div className="skill-grid">
              {data.spin_analysis && (
                <div>
                  <span className="eyebrow">SPIN</span>
                  <p className="muted" style={{ marginTop: 10, fontSize: 13, lineHeight: 1.7 }}>{data.spin_analysis}</p>
                </div>
              )}
              {data.batna_analysis && (
                <div>
                  <span className="eyebrow">BATNA</span>
                  <p className="muted" style={{ marginTop: 10, fontSize: 13, lineHeight: 1.7 }}>{data.batna_analysis}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {(data.strengths?.length || data.weaknesses?.length || data.suggestions?.length) ? (
        <div className="card" style={{ marginTop: 16, padding: 24 }}>
          <div className="skill-grid">
            {data.strengths?.length > 0 && (
              <div>
                <span className="eyebrow">Сильные стороны</span>
                <ul style={{ marginTop: 10, paddingLeft: 18, fontSize: 13, lineHeight: 1.7 }}>
                  {data.strengths.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              </div>
            )}
            {data.weaknesses?.length > 0 && (
              <div>
                <span className="eyebrow">Слабые места</span>
                <ul style={{ marginTop: 10, paddingLeft: 18, fontSize: 13, lineHeight: 1.7 }}>
                  {data.weaknesses.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              </div>
            )}
            {data.suggestions?.length > 0 && (
              <div>
                <span className="eyebrow">Рекомендации</span>
                <ul style={{ marginTop: 10, paddingLeft: 18, fontSize: 13, lineHeight: 1.7 }}>
                  {data.suggestions.map((s, i) => <li key={i}>{s}</li>)}
                </ul>
              </div>
            )}
          </div>
        </div>
      ) : null}

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 16 }}>
        <button className="btn btn-primary" onClick={() => navigate('/catalog')} data-testid="button-retry">
          <RotateCcw size={15} /> Новая тренировка
        </button>
        <button className="btn btn-quiet" onClick={() => navigate('/profile')} data-testid="button-finish-analytics">
          В профиль <ArrowRight size={15} />
        </button>
      </div>
    </>
  );
}
