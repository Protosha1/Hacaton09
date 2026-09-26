// Онбординг (выбор направлений и опыта для новичка).
import { useState } from 'react';
import { Redirect, useLocation } from 'wouter';
import { ArrowLeft, ArrowRight, Check } from 'lucide-react';
import { categories, experienceLevels } from '@/data/categories';
import { useAuth } from '@/context/AuthContext';

export default function Onboarding() {
  const { user, completeOnboarding } = useAuth();
  const [, navigate] = useLocation();
  const [step, setStep] = useState(1);
  const [selected, setSelected] = useState([]);
  const [experience, setExperience] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!user) return <Redirect to="/register" />;
  if (user.status === 'active') return <Redirect to="/profile" />;

  const toggle = (key) => setSelected((items) => (items.includes(key) ? items.filter((k) => k !== key) : items.length < 3 ? [...items, key] : items));

  const finish = async () => {
    if (!experience || !selected.length) return;
    setSubmitting(true);
    setError('');
    try {
      await completeOnboarding(selected, experience);
      const pendingInvite = sessionStorage.getItem('negotiator-pending-invite');
      navigate(pendingInvite ? `/invite/${pendingInvite}` : '/profile');
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-wrap">
      <div className="card auth-card" style={{ maxWidth: 620 }}>
        <span className="eyebrow">Настройка арены · шаг {step} из 2</span>
        <div className="stepper"><span className="active" /><span className={step === 2 ? 'active' : ''} /></div>
        {step === 1 ? (
          <>
            <h1 className="display">О чём хотите говорить увереннее?</h1>
            <p className="muted">Выберите от одной до трёх ситуаций. Это настроит вашу первую подборку.</p>
            <div className="category-grid" style={{ gridTemplateColumns: 'repeat(2,1fr)', marginTop: 25 }}>
              {categories.map(({ key, name, icon: Icon }) => (
                <button
                  className={`option ${selected.includes(key) ? 'selected' : ''}`}
                  key={key}
                  onClick={() => toggle(key)}
                  style={{ minHeight: 78 }}
                  data-testid={`button-category-${key}`}
                >
                  <Icon size={17} />
                  <span style={{ display: 'block', marginTop: 12 }}>{name}</span>
                  {selected.includes(key) && <Check size={15} style={{ float: 'right', color: '#9de3e5' }} />}
                </button>
              ))}
            </div>
            <button
              className="btn btn-primary"
              disabled={!selected.length}
              onClick={() => setStep(2)}
              style={{ marginTop: 24, width: '100%' }}
              data-testid="button-onboarding-next"
            >
              Продолжить <ArrowRight size={16} />
            </button>
          </>
        ) : (
          <>
            <h1 className="display">Какой у вас опыт?</h1>
            <p className="muted">Мы подберём первый уровень нагрузки. Его можно изменить перед каждой тренировкой.</p>
            <div style={{ display: 'grid', gap: 10, marginTop: 25 }}>
              {experienceLevels.map((item) => (
                <button
                  className={`option ${experience === item.value ? 'selected' : ''}`}
                  key={item.value}
                  onClick={() => setExperience(item.value)}
                  style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                  data-testid={`button-experience-${item.value}`}
                >
                  {item.label}
                  <span className="muted">{item.hint}</span>
                  {experience === item.value && <Check size={15} />}
                </button>
              ))}
            </div>
            {error && <span className="form-error">{error}</span>}
            <div style={{ display: 'flex', gap: 10, marginTop: 24 }}>
              <button className="btn btn-quiet" onClick={() => setStep(1)}><ArrowLeft size={16} /> Назад</button>
              <button
                className="btn btn-primary"
                disabled={!experience || submitting}
                onClick={finish}
                style={{ flex: 1 }}
                data-testid="button-onboarding-finish"
              >
                {submitting ? 'Сохраняем…' : <>Войти в профиль <ArrowRight size={16} /></>}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
