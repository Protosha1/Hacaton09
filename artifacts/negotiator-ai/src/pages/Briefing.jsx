// Брифинг: описание ситуации и цели перед стартом переговоров.
import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'wouter';
import { ArrowRight, Mic } from 'lucide-react';
import { negotiationApi } from '@/lib/api';
import { difficultyLabels, difficultyXp } from '@/data/categories';

// Сколько миллисекунд слушаем микрофон при проверке и порог RMS-громкости,
// выше которого считаем, что звук реально пойман (а не просто есть доступ).
const MIC_TEST_DURATION_MS = 2500;
const MIC_SILENCE_THRESHOLD = 0.02;

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

  // idle -> testing -> ok | silent | error
  const [micStatus, setMicStatus] = useState('idle');
  const [micLevel, setMicLevel] = useState(0);
  const micStreamRef = useRef(null);
  const micRafRef = useRef(null);
  const micCtxRef = useRef(null);

  const stopMicTest = () => {
    if (micRafRef.current) cancelAnimationFrame(micRafRef.current);
    micRafRef.current = null;
    micStreamRef.current?.getTracks().forEach((t) => t.stop());
    micStreamRef.current = null;
    if (micCtxRef.current) {
      micCtxRef.current.close().catch(() => {});
      micCtxRef.current = null;
    }
  };

  useEffect(() => () => stopMicTest(), []);

  // Реальная проверка микрофона: запрашиваем доступ и слушаем громкость
  // несколько секунд, а не просто проверяем, что permission выдан — так мы
  // ловим случаи вроде "разрешение есть, но выбран не тот/немой микрофон".
  const checkMic = async () => {
    stopMicTest();
    setMicStatus('testing');
    setMicLevel(0);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      micStreamRef.current = stream;
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioCtx();
      micCtxRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 512;
      source.connect(analyser);
      const data = new Uint8Array(analyser.frequencyBinCount);

      let maxLevel = 0;
      const start = performance.now();

      const tick = () => {
        analyser.getByteTimeDomainData(data);
        let sum = 0;
        for (let i = 0; i < data.length; i += 1) {
          const v = (data[i] - 128) / 128;
          sum += v * v;
        }
        const rms = Math.sqrt(sum / data.length);
        maxLevel = Math.max(maxLevel, rms);
        setMicLevel(Math.min(1, rms * 4));

        if (performance.now() - start < MIC_TEST_DURATION_MS) {
          micRafRef.current = requestAnimationFrame(tick);
        } else {
          stopMicTest();
          setMicLevel(0);
          setMicStatus(maxLevel > MIC_SILENCE_THRESHOLD ? 'ok' : 'silent');
        }
      };
      tick();
    } catch (err) {
      stopMicTest();
      setMicStatus('error');
    }
  };

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

      <div className="card" style={{ padding: 20, background: 'rgba(17,14,37,0.9)' }}>
        <span className="eyebrow">Ваша цель</span>
        <p style={{ margin: '12px 0 0', lineHeight: 1.6 }}>{briefing.user_goal}</p>
      </div>

      <div className="mic-check">
        <div className="mic-icon"><Mic size={20} /></div>
        <div style={{ flex: 1 }}>
          <strong>Вы будете говорить вслух с {briefing.opponent_role || 'собеседником'}</strong>
          <p className="muted" style={{ fontSize: 12, margin: '5px 0 8px' }}>
            Разрешите доступ к микрофону и скажите пару слов — Fastur распознает вашу речь, а собеседник ответит текстом.
          </p>

          {micStatus === 'idle' && (
            <button type="button" className="btn btn-quiet" style={{ fontSize: 12 }} onClick={checkMic} data-testid="button-check-mic">
              Проверить микрофон
            </button>
          )}

          {micStatus === 'testing' && (
            <div>
              <div className="mic-level-bar"><div className="mic-level-fill" style={{ width: `${micLevel * 100}%` }} /></div>
              <p className="muted" style={{ fontSize: 12, margin: '6px 0 0' }}>Скажите что-нибудь вслух…</p>
            </div>
          )}

          {micStatus === 'ok' && (
            <p style={{ fontSize: 12, margin: 0, color: '#7be3a0' }} data-testid="text-mic-ok">✓ Микрофон работает, слышно хорошо</p>
          )}

          {micStatus === 'silent' && (
            <div>
              <p className="form-error" style={{ fontSize: 12, margin: '0 0 6px' }}>
                Доступ к микрофону есть, но звук не пойман. Проверьте, что выбран нужный микрофон, и скажите погромче.
              </p>
              <button type="button" className="btn btn-quiet" style={{ fontSize: 12 }} onClick={checkMic}>Повторить проверку</button>
            </div>
          )}

          {micStatus === 'error' && (
            <div>
              <p className="form-error" style={{ fontSize: 12, margin: '0 0 6px' }}>
                Не удалось получить доступ к микрофону. Разрешите доступ в настройках браузера и попробуйте снова.
              </p>
              <button type="button" className="btn btn-quiet" style={{ fontSize: 12 }} onClick={checkMic}>Повторить проверку</button>
            </div>
          )}
        </div>
      </div>

      {error && <span className="form-error">{error}</span>}

      <button
        className="btn btn-primary"
        style={{ width: '100%' }}
        disabled={starting || micStatus !== 'ok'}
        onClick={start}
        data-testid="button-start-session"
      >
        {starting ? 'Начинаем…' : <>Начать разговор <ArrowRight size={16} /></>}
      </button>
      {micStatus !== 'ok' && (
        <p className="muted" style={{ fontSize: 11, marginTop: 8, textAlign: 'center' }}>
          Сначала пройдите проверку микрофона, чтобы начать разговор.
        </p>
      )}
    </div>
  );
}
