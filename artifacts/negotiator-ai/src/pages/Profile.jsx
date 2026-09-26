// Личный кабинет пользователя: прогресс, рекомендации, история разговоров.
import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import { ArrowRight, ChevronRight, Play } from 'lucide-react';
import { negotiationApi, usersApi } from '@/lib/api';
import { categoryLabel } from '@/data/categories';

// Пороги рангов — зеркалят backend (app/core/xp.py RANKS), т.к. API отдаёт
// только total_xp и rank_level/rank_name, без готового процента до следующего.
const RANKS = [
  { level: 1, minXp: 0, maxXp: 100 },
  { level: 2, minXp: 100, maxXp: 400 },
  { level: 3, minXp: 400, maxXp: 700 },
  { level: 4, minXp: 700, maxXp: 1200 },
];

function xpProgress(totalXp = 0, rankLevel = 1) {
  const rank = RANKS.find((r) => r.level === rankLevel) || RANKS[RANKS.length - 1];
  const isMax = rank.level === RANKS[RANKS.length - 1].level;
  const span = rank.maxXp - rank.minXp;
  const percent = isMax ? 100 : Math.min(100, Math.max(0, ((totalXp - rank.minXp) / span) * 100));
  return { percent, isMax, xpToNext: isMax ? 0 : Math.max(0, rank.maxXp - totalXp) };
}

const skillLabels = {
  emotion_control: 'Управление эмоциями',
  batna: 'BATNA (запасной план)',
  spin: 'SPIN (вопросы)',
};

export default function Profile({ user, onToast }) {
  const [, navigate] = useLocation();
  const [progress, setProgress] = useState(null);
  const [skills, setSkills] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [interrupted, setInterrupted] = useState(null);
  const [showHistory, setShowHistory] = useState(false);

  useEffect(() => {
    if (!user?.id) return;
    negotiationApi.progress(user.id).then(setProgress).catch(() => {});
    usersApi.skills(user.id).then((r) => setSkills(r.skills || [])).catch(() => {});
    negotiationApi.sessions(user.id).then(setSessions).catch(() => {});
    usersApi.recommendations(user.id, 3).then((r) => setRecommendations(r.recommendations || [])).catch(() => {});
    usersApi.interruptedSession(user.id).then((r) => setInterrupted(r.has_interrupted ? r.session : null)).catch(() => {});
  }, [user?.id]);

  const visibleHistory = showHistory ? sessions : sessions.slice(0, 1);
  const firstName = user.name?.split(' ')[0] || user.email.split('@')[0];
  const progressBar = xpProgress(user.total_xp, user.rank_level);

  const resumeInterrupted = () => {
    if (interrupted?.scenario_id) navigate(`/constructor?case=${interrupted.scenario_id}`);
    else navigate('/catalog');
  };

  return (
    <>
      <div className="page-header">
        <div>
          <span className="eyebrow">Профиль · {user.rank_name}</span>
          <h1 className="display">Ваш прогресс, {firstName}.</h1>
          <p className="muted">Результат появляется не из уверенности. Он появляется из повторений.</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/constructor')} data-testid="button-new-session">
          <Play size={15} /> Новая тренировка
        </button>
      </div>

      <div className="dashboard-grid">
        <div className="card profile-hero">
          <div className="avatar" data-testid="img-avatar">
            {(user.name || user.email).split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="eyebrow">Ваш ранг</div>
            <h2 style={{ margin: '8px 0 5px', fontSize: 25 }}>{user.rank_name}</h2>
            <span className="muted" style={{ fontSize: 13 }}>
              {user.directions?.length ? user.directions.map(categoryLabel).join(' · ') : 'Выберите фокус в каталоге'}
            </span>
          </div>
        </div>

        <div className="card rank-card">
          <div className="rank-number">ВСЕГО НАКОПЛЕНО XP</div>
          <div className="xp">{user.total_xp} <span style={{ fontSize: 14, color: '#aaa2c2' }}>XP</span></div>
          <div className="progress"><i style={{ width: `${progressBar.percent}%` }} /></div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 9, fontSize: 11 }}>
            <span className="muted">Уровень {user.rank_level}</span>
            <span className="muted">
              {progressBar.isMax ? 'Максимальный ранг' : `Ещё ${progressBar.xpToNext} XP до следующего`}
            </span>
          </div>
        </div>

        {interrupted ? (
          <div className="card recommendation">
            <span className="eyebrow">Незавершённый разговор</span>
            <h3>{interrupted.scenario_name || 'Незавершённый разговор'}</h3>
            <p className="muted" style={{ fontSize: 12 }}>
              Продолжить с того же места нельзя — но вы можете начать этот кейс заново.
            </p>
            <button className="btn btn-small btn-primary" onClick={resumeInterrupted} data-testid="button-resume">
              Начать заново <ArrowRight size={14} />
            </button>
          </div>
        ) : (
          <div className="card recommendation">
            <span className="eyebrow">Рекомендация</span>
            <h3>{recommendations[0]?.name || 'Потренируйте новый навык'}</h3>
            <p className="muted" style={{ fontSize: 12, lineHeight: 1.5 }}>
              {recommendations[0]?.description || 'Загляните в каталог — там есть кейсы под ваш фокус.'}
            </p>
            <button className="btn btn-quiet btn-small" onClick={() => navigate('/catalog')}>
              Открыть каталог <ArrowRight size={14} />
            </button>
          </div>
        )}

        <div className="card">
          <div className="history">
            <span className="eyebrow">Средний результат</span>
            <h3 style={{ margin: '13px 0 7px', fontSize: 20 }}>
              {progress?.average_overall != null ? `${Math.round(progress.average_overall)} / 100` : 'Ещё нет данных'}
            </h3>
            <p className="muted" style={{ fontSize: 12, lineHeight: 1.5 }}>
              {progress ? `${progress.finished_sessions} завершённых сессий из ${progress.total_sessions}.` : 'Пройдите первую тренировку, чтобы увидеть статистику.'}
            </p>
          </div>
        </div>
      </div>

      <section style={{ marginTop: 16 }}>
        <div className="card history">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span className="eyebrow">Последние попытки</span>
              <h2 style={{ margin: '10px 0 0', fontSize: 22 }}>История разговоров</h2>
            </div>
            {sessions.length > 1 && (
              <button className="btn btn-quiet btn-small" onClick={() => setShowHistory(!showHistory)}>
                {showHistory ? 'Свернуть' : 'Вся история'} <ChevronRight size={14} />
              </button>
            )}
          </div>
          <div className="history-list">
            {visibleHistory.length === 0 && <p className="muted" style={{ padding: '14px 0' }}>Пока нет завершённых тренировок.</p>}
            {visibleHistory.map((s) => (
              <div className="history-row" key={s.session_id}>
                <strong>{s.scenario_name || 'Сценарий удалён'}</strong>
                <span className="muted">{new Date(s.created_at).toLocaleDateString('ru-RU')}</span>
                <span className="verdict">{s.status === 'finished' ? 'Завершено' : s.status === 'interrupted' ? 'Прервано' : 'В процессе'}</span>
                <strong>{s.overall_score != null ? `${s.overall_score} баллов` : '—'}</strong>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section style={{ marginTop: 16 }}>
        <div className="card" style={{ padding: 25 }}>
          <span className="eyebrow">Карта навыков</span>
          <h2 style={{ margin: '10px 0 20px', fontSize: 22 }}>То, что уже становится привычкой.</h2>
          <div className="skill-grid">
            {(skills.length ? skills : Object.keys(skillLabels).map((metric) => ({ metric, current_value: 0, sessions_count: 0 }))).map((skill) => (
              <div className="skill-card" key={skill.metric} style={{ background: 'rgba(17,14,37,.28)', borderRadius: 15 }}>
                <span className="muted" style={{ fontSize: 12 }}>{skillLabels[skill.metric] || skill.metric}</span>
                <div className="skill-score">{skill.current_value}%</div>
                <span className="muted" style={{ fontSize: 11 }}>{skill.sessions_count} сессий</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
