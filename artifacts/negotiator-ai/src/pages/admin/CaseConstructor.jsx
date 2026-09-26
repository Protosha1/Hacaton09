// Конструктор кейса для админа: создание и редактирование сценария,
// затем публикация (получение ссылки-приглашения).
import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import { ArrowLeft, ArrowRight, Check, Info } from 'lucide-react';
import { categories } from '@/data/categories';
import { scenariosApi } from '@/lib/api';

export default function AdminCaseNew({ onToast }) {
  const [, navigate] = useLocation();
  const editId = new URLSearchParams(window.location.search).get('edit');

  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(!!editId);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const [name, setName] = useState('');
  const [category, setCategory] = useState(categories[0].key);
  const [description, setDescription] = useState('');
  const [userRole, setUserRole] = useState('');
  const [userGoal, setUserGoal] = useState('');
  const [opponentRole, setOpponentRole] = useState('');
  const [opponentCharacter, setOpponentCharacter] = useState('');
  const [opponentGoal, setOpponentGoal] = useState('');
  const [toneBehavior, setToneBehavior] = useState('');
  const [initialMessage, setInitialMessage] = useState('');
  const [priceMin, setPriceMin] = useState('');

  useEffect(() => {
    if (!editId) return;
    scenariosApi.mine().then((list) => {
      const existing = list.find((item) => item.id === editId);
      if (!existing) return;
      setName(existing.name || '');
      setCategory(existing.category || categories[0].key);
      setDescription(existing.description || '');
      setUserRole(existing.user_role || '');
      setUserGoal(existing.user_goal || '');
      setOpponentRole(existing.opponent_role || '');
      setOpponentCharacter(existing.opponent_character || '');
      setOpponentGoal(existing.opponent_goal || '');
      setToneBehavior(existing.tone_behavior || '');
      setInitialMessage(existing.initial_message || '');
      setPriceMin(existing.concession_limits?.price_min ?? '');
    }).finally(() => setLoading(false));
  }, [editId]);

  const buildPayload = () => ({
    name: name || 'Новый переговорный сценарий',
    category,
    description,
    user_role: userRole,
    user_goal: userGoal,
    opponent_role: opponentRole,
    opponent_character: opponentCharacter,
    opponent_goal: opponentGoal,
    tone_behavior: toneBehavior,
    initial_message: initialMessage,
    concession_limits: priceMin !== '' ? { price_min: Number(priceMin) } : undefined,
  });

  const save = async (publish) => {
    setSaving(true);
    setError('');
    try {
      const payload = buildPayload();
      const saved = editId ? await scenariosApi.update(editId, payload) : await scenariosApi.create(payload);
      if (publish) {
        await scenariosApi.publish(saved.id || editId);
        onToast?.('Кейс сохранён и опубликован — ссылка готова в списке кейсов');
      } else {
        onToast?.(editId ? 'Кейс обновлён' : 'Черновик сохранён');
      }
      navigate('/admin/cases');
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p className="muted">Загружаем кейс…</p>;

  return (
    <>
      <div className="page-header">
        <div>
          <span className="eyebrow">{editId ? 'Редактирование' : 'Новый кейс'} · шаг {step} из 2</span>
          <h1 className="display">Соберите ситуацию для команды.</h1>
        </div>
        <button className="btn btn-quiet" onClick={() => navigate('/admin/cases')}><ArrowLeft size={15} /> Отмена</button>
      </div>

      <div className="stepper"><span className="active" /><span className={step === 2 ? 'active' : ''} /></div>

      <div className="card form-card" style={{ maxWidth: 760 }}>
        {step === 1 ? (
          <>
            <div className="field">
              <label htmlFor="admin-title">Название кейса</label>
              <input id="admin-title" value={name} onChange={(e) => setName(e.target.value)} placeholder="Например: Обсуждение бюджета проекта" data-testid="input-admin-title" />
            </div>
            <div className="field" style={{ marginTop: 18 }}>
              <label htmlFor="admin-category">Категория</label>
              <select id="admin-category" value={category} onChange={(e) => setCategory(e.target.value)}>
                {categories.map((c) => <option key={c.key} value={c.key}>{c.name}</option>)}
              </select>
            </div>
            <div className="field" style={{ marginTop: 18 }}>
              <label htmlFor="admin-description">Ситуация</label>
              <textarea id="admin-description" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Что произошло до начала разговора?" />
            </div>
            <div className="field" style={{ marginTop: 18 }}>
              <label htmlFor="admin-user-role">Роль участника</label>
              <input id="admin-user-role" value={userRole} onChange={(e) => setUserRole(e.target.value)} placeholder="Например: Менеджер по продажам" />
            </div>
            <div className="field" style={{ marginTop: 18 }}>
              <label htmlFor="admin-opponent-role">Роль оппонента</label>
              <input id="admin-opponent-role" value={opponentRole} onChange={(e) => setOpponentRole(e.target.value)} placeholder="Например: Клиент" />
            </div>
            <button className="btn btn-primary" style={{ marginTop: 23 }} onClick={() => setStep(2)} data-testid="button-admin-next">
              Дальше <ArrowRight size={16} />
            </button>
          </>
        ) : (
          <>
            <div className="field">
              <label htmlFor="admin-goal">Цель участника</label>
              <textarea id="admin-goal" value={userGoal} onChange={(e) => setUserGoal(e.target.value)} placeholder="Какой результат должен получить участник?" />
            </div>
            <div className="field" style={{ marginTop: 18 }}>
              <label htmlFor="admin-opp-character">Характер оппонента (со спойлером)</label>
              <textarea id="admin-opp-character" value={opponentCharacter} onChange={(e) => setOpponentCharacter(e.target.value)} placeholder="Как оппонент себя ведёт, чего избегает" />
            </div>
            <div className="field" style={{ marginTop: 18 }}>
              <label htmlFor="admin-opp-goal">Цель оппонента (со спойлером)</label>
              <textarea id="admin-opp-goal" value={opponentGoal} onChange={(e) => setOpponentGoal(e.target.value)} placeholder="Чего на самом деле хочет оппонент" />
            </div>
            <div className="field" style={{ marginTop: 18 }}>
              <label htmlFor="admin-tone">Тон / поведение оппонента <span className="muted">(обязательно для публикации)</span></label>
              <input id="admin-tone" value={toneBehavior} onChange={(e) => setToneBehavior(e.target.value)} placeholder="Например: Жёсткий, но справедливый" data-testid="input-tone-behavior" />
            </div>
            <div className="field" style={{ marginTop: 18 }}>
              <label htmlFor="admin-price-min">Минимальная граница уступки, число <span className="muted">(обязательно для публикации)</span></label>
              <input id="admin-price-min" type="number" value={priceMin} onChange={(e) => setPriceMin(e.target.value)} placeholder="Например: 100" data-testid="input-price-min" />
            </div>
            <div className="field" style={{ marginTop: 18 }}>
              <label htmlFor="admin-initial">Первая реплика оппонента</label>
              <textarea id="admin-initial" value={initialMessage} onChange={(e) => setInitialMessage(e.target.value)} placeholder="Чем оппонент открывает разговор" />
            </div>

            <div className="card" style={{ marginTop: 22, padding: 17, background: 'rgba(20,38,40,0.94)', borderColor: 'rgba(157,227,229,.3)' }}>
              <div style={{ display: 'flex', gap: 10 }}>
                <Info size={17} color="#9de3e5" />
                <span className="soft" style={{ fontSize: 12, lineHeight: 1.5 }}>
                  Можно сохранить как черновик и опубликовать позже, или опубликовать сразу — тогда кейс сразу получит ссылку-приглашение.
                </span>
              </div>
            </div>

            {error && <span className="form-error">{error}</span>}

            <div style={{ display: 'flex', gap: 10, marginTop: 23, flexWrap: 'wrap' }}>
              <button className="btn btn-quiet" onClick={() => setStep(1)} disabled={saving}><ArrowLeft size={15} /> Назад</button>
              <button className="btn" onClick={() => save(false)} disabled={saving} style={{ flex: 1 }} data-testid="button-save-draft">
                {saving ? 'Сохраняем…' : 'Сохранить как черновик'}
              </button>
              <button className="btn btn-primary" onClick={() => save(true)} disabled={saving} style={{ flex: 1 }} data-testid="button-save-admin-case">
                <Check size={15} /> {saving ? 'Публикуем…' : 'Сохранить и опубликовать'}
              </button>
            </div>
          </>
        )}
      </div>
    </>
  );
}
