import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import { Plus } from 'lucide-react';
import { categories } from '@/data/categories';
import { scenariosApi, usersApi } from '@/lib/api';
import CategoryAccordion from '@/components/CategoryAccordion';

export default function Catalog({ user, onToast }) {
  const [, navigate] = useLocation();
  const [open, setOpen] = useState(categories[0].key);
  const [scenarios, setScenarios] = useState([]);
  const [addedCases, setAddedCases] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    scenariosApi
      .list()
      .then((list) => { if (!cancelled) setScenarios(list); })
      .catch(() => onToast?.('Не удалось загрузить каталог. Backend доступен?'))
      .finally(() => { if (!cancelled) setLoading(false); });
    if (user?.id) {
      usersApi.addedCases(user.id).then((res) => { if (!cancelled) setAddedCases(res.cases || []); }).catch(() => {});
    }
    return () => { cancelled = true; };
  }, [user?.id]);

  const openCase = (item) => {
    if (user) navigate(`/constructor?case=${item.id}`);
    else onToast?.('Войдите, чтобы открыть конструктор');
  };

  return (
    <>
      <div className="page-header">
        <div>
          <span className="eyebrow">Каталог</span>
          <h1 className="display">Выберите переговорный маршрут.</h1>
          <p className="muted">Шесть областей. В каждой — разговоры, которые встречаются в рабочем календаре.</p>
        </div>
        {user && (
          <button className="btn btn-primary" onClick={() => navigate('/constructor')}>
            <Plus size={15} /> Собрать тренировку
          </button>
        )}
      </div>

      {loading ? (
        <p className="muted">Загружаем кейсы…</p>
      ) : (
        <div className="catalog-grid">
          {categories.map((category) => (
            <CategoryAccordion
              key={category.key}
              category={category}
              cases={scenarios.filter((item) => item.category === category.key)}
              expanded={open === category.key}
              onToggle={() => setOpen(open === category.key ? null : category.key)}
              actionLabel={user ? 'Открыть' : 'Детали'}
              onCaseAction={openCase}
            />
          ))}

          {user && (
            <CategoryAccordion
              category={{ key: 'added', name: 'Добавленные', icon: Plus, description: 'Ваши сохранённые кейсы, добавленные по ссылке-приглашению.' }}
              cases={addedCases.map((c) => ({ ...c, id: c.case_id, name: c.name }))}
              expanded={open === 'added'}
              onToggle={() => setOpen(open === 'added' ? null : 'added')}
              actionLabel="Открыть"
              onCaseAction={openCase}
              emptyHint="Пока нет добавленных кейсов — примите ссылку-приглашение от автора."
            />
          )}
        </div>
      )}
    </>
  );
}
