// Конструктор: выбор кейса, сложности и условий переговоров.
import { useEffect, useState } from 'react';
import { Link, useLocation } from 'wouter';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { categories, categoryLabel, difficultyLabels, difficultyXp, experienceLevels } from '@/data/categories';
import { scenariosApi, usersApi } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';

const relationshipOptions = [
  { value: 'stranger', label: 'Незнакомец' },
  { value: 'colleague', label: 'Коллега' },
  { value: 'friend', label: 'Приятель' },
  { value: 'boss', label: 'Руководитель' },
  { value: 'subordinate', label: 'Подчинённый' },
];

const powerBalanceOptions = [
  { value: 'user_strong', label: 'Сила на вашей стороне' },
  { value: 'equal', label: 'Равные позиции' },
  { value: 'opponent_strong', label: 'Сила у собеседника' },
];

export default function ConstructorPage() {
  const { user } = useAuth();
  const [, navigate] = useLocation();
  const params = new URLSearchParams(window.location.search);

  const [scenarios, setScenarios] = useState([]);
  const [category, setCategory] = useState(categories[0].key);
  const [caseId, setCaseId] = useState(params.get('case') || '');
  const [difficulty, setDifficulty] = useState(user?.experience_level || 'practitioner');
  const [relationship, setRelationship] = useState('colleague');
  const [powerBalance, setPowerBalance] = useState('equal');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      scenariosApi.list(),
      user?.id ? usersApi.addedCases(user.id).then((r) => r.cases || []).catch(() => []) : Promise.resolve([]),
    ]).then(([publicList, added]) => {
      // Публичный каталог + кейсы, добавленные по ссылке-приглашению
      // (иначе их невозможно было бы выбрать и сыграть).
      const addedAsScenarios = added.map((c) => ({ ...c, id: c.case_id }));
      const byId = new Map();
      [...publicList, ...addedAsScenarios].forEach((s) => byId.set(s.id, s));
      const list = Array.from(byId.values());
      setScenarios(list);
      const preset = params.get('case') && list.find((s) => s.id === params.get('case'));
      if (preset) {
        setCategory(preset.category || categories[0].key);
        setCaseId(preset.id);
      } else if (list.length) {
        setCategory(list[0].category || categories[0].key);
        setCaseId(list[0].id);
      }
    }).finally(() => setLoading(false));
  }, [user?.id]);

  const categoryCases = scenarios.filter((s) => s.category === category);
  const selected = scenarios.find((s) => s.id === caseId) || categoryCases[0] || scenarios[0];

  useEffect(() => {
    if (categoryCases.length && !categoryCases.some((s) => s.id === caseId)) {
      setCaseId(categoryCases[0].id);
    }
  }, [category]);

  const goToBriefing = () => {
    if (!selected) return;
    const qs = new URLSearchParams({ case: selected.id, difficulty, relationship, power_balance: powerBalance });
    navigate(`/briefing?${qs.toString()}`);
  };

  if (loading) return <p className="muted">Загружаем кейсы…</p>;

  if (!scenarios.length) {
    return (
      <div className="card" style={{ padding: 24 }}>
        <p className="muted">В каталоге пока нет опубликованных кейсов. Попросите администратора создать и опубликовать сценарий.</p>
      </div>
    );
  }

  return (
    <>
      <div className="page-header">
        <div>
          <span className="eyebrow">Конструктор</span>
          <h1 className="display">Соберите разговор под себя.</h1>
          <p className="muted">Настройка займёт меньше минуты. После неё — брифинг и диалог с AI.</p>
        </div>
        <Link href="/catalog" className="btn btn-quiet"><ArrowLeft size={15} /> Каталог</Link>
      </div>

      <div className="constructor-grid">
        <div className="card form-card">
          <div className="field">
            <label htmlFor="category">Категория</label>
            <select id="category" value={category} onChange={(e) => setCategory(e.target.value)} data-testid="select-category">
              {categories.map((c) => <option key={c.key} value={c.key}>{c.name}</option>)}
            </select>
          </div>

          <div className="field" style={{ marginTop: 20 }}>
            <label htmlFor="case">Кейс</label>
            <select id="case" value={caseId} onChange={(e) => setCaseId(e.target.value)} data-testid="select-case">
              {(categoryCases.length ? categoryCases : scenarios).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
            </select>
          </div>

          <div className="field" style={{ marginTop: 20 }}>
            <label>Сложность</label>
            <div className="option-grid">
              {experienceLevels.map((item) => (
                <button
                  key={item.value}
                  className={`option ${difficulty === item.value ? 'selected' : ''}`}
                  onClick={() => setDifficulty(item.value)}
                  data-testid={`button-difficulty-${item.value}`}
                >
                  {item.label}
                  <span style={{ display: 'block', color: '#9de3e5', fontFamily: 'DM Mono', marginTop: 7 }}>
                    +{difficultyXp[item.value]} XP
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="field" style={{ marginTop: 20 }}>
            <label htmlFor="relationship">Отношения с собеседником</label>
            <select id="relationship" value={relationship} onChange={(e) => setRelationship(e.target.value)}>
              {relationshipOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>

          <div className="field" style={{ marginTop: 20 }}>
            <label htmlFor="power">Баланс сил</label>
            <select id="power" value={powerBalance} onChange={(e) => setPowerBalance(e.target.value)}>
              {powerBalanceOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>

          <button className="btn btn-primary" style={{ width: '100%', marginTop: 22 }} onClick={goToBriefing} data-testid="button-to-briefing">
            Перейти к брифингу <ArrowRight size={16} />
          </button>
        </div>

        <div className="card" style={{ padding: 28, minHeight: 400, background: 'radial-gradient(circle at 80% 10%,rgba(188,160,255,.25),transparent 42%),rgba(39,32,72,0.96)' }}>
          <span className="eyebrow">Предпросмотр</span>
          <h2 className="display" style={{ fontSize: 36, margin: '21px 0 12px' }}>{selected?.name}</h2>
          <p className="soft" style={{ lineHeight: 1.65, fontSize: 14 }}>{selected?.description}</p>
          {selected?.opponent_role && (
            <div style={{ marginTop: 25 }}>
              <span className="eyebrow">Собеседник</span>
              <p className="soft" style={{ fontSize: 14 }}>{selected.opponent_role}</p>
            </div>
          )}
          <div style={{ display: 'flex', gap: 8, marginTop: 25, flexWrap: 'wrap' }}>
            <span className="tag">{categoryLabel(category)}</span>
            <span className="tag tag-warm">{difficultyLabels[difficulty]}</span>
          </div>
        </div>
      </div>
    </>
  );
}
