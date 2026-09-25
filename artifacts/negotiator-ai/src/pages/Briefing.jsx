// Брифинг: описание ситуации и цели перед стартом переговоров.
import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import { ArrowRight, Mic } from 'lucide-react';
import { negotiationApi } from '@/lib/api';
import { difficultyLabels, difficultyXp } from '@/data/categories';

export default function Briefing() {
  const [, navigate] = useLocation();
  const params = new URLSearchParams(window.location.search);
  const scenarioId = params.get('case');
  const difficulty = params.get('difficulty') || 'practitioner';
  const relationship = params.get('relationship') || 'colleague';
  const powerBalance = params.get('power_balance') || 'equal';

  const [briefing, setBriefing] = useState(null);
  const [error, setError] = useState('');
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    if (!scenarioId) return;
    negotiationApi.briefing(scenarioId).then(setBriefing).catch((err) => setError(err.message));
  }, [scenarioId]);

  const start = async () => {
    setStarting(true);
    setError('');
    try {
      const session = await negotiationApi.start({
        scenario_id: scenarioId,
        difficulty,
        relationship,
        power_balance: powerBalance,
      });
      sessionStorage.setItem('negotiator-active-session', JSON.stringify({
        ...session,
        scenario_name: briefing?.name,
      }));
      navigate('/session');
    } catch (err) {
      setError(err.message);
    } finally {
      setStarting(false);
    }
  };

  if (!scenarioId) {
    return <div className="card" style={{ padding: 24 }}><p className="muted">Кейс не выбран. Вернитесь в каталог.</p></div>;
  }

  if (error && !briefing) {
    return <div className="card" style={{ padding: 24 }}><p className="muted">{error}</p></div>;
  }

  if (!briefing) return <p className="muted">Загружаем брифинг…</p>;

  return (
    <div className="briefing-card card">
      <span className="eyebrow">Брифинг · 2 минуты</span>
      <h1 className="display" style={{ fontSize: 'clamp(34px,5vw,58px)', margin: '18px 0 14px' }}>Войдите в разговор с ясной целью.</h1>
      <p className="muted" style={{ maxWidth: 650, lineHeight: 1.65 }}>{briefing.description}</p>

      <div className="briefing-meta">
        <div className="meta-box"><small>СЦЕНАРИЙ</small><strong>{briefing.name}</strong></div>
        <div className="meta-box"><small>СЛОЖНОСТЬ</small><strong>{difficultyLabels[difficulty]}</strong></div>
        <div className="meta-box"><small>БАЗОВАЯ НАГРАДА</small><strong>{difficultyXp[difficulty]} XP</strong></div>
      </div>

      <div className="card" style={{ padding: 20, background: 'rgba(17,14,37,.28)' }}>
        <span className="eyebrow">Ваша цель</span>
        <p style={{ margin: '12px 0 0', lineHeight: 1.6 }}>{briefing.user_goal}</p>
      </div>

      <div className="mic-check">
        <div className="mic-icon"><Mic size={20} /></div>
        <div style={{ flex: 1 }}>
          <strong>Вы будете говорить вслух с {briefing.opponent_role || 'собеседником'}</strong>
          <p className="muted" style={{ fontSize: 12, margin: '5px 0 0' }}>Разрешите доступ к микрофону — Fastur распознает вашу речь, а собеседник ответит текстом.</p>
        </div>
      </div>

      {error && <span className="form-error">{error}</span>}

      <button className="btn btn-primary" style={{ width: '100%' }} disabled={starting} onClick={start} data-testid="button-start-session">
        {starting ? 'Начинаем…' : <>Начать разговор <ArrowRight size={16} /></>}
      </button>
    </div>
  );
}
