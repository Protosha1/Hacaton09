import { ChevronDown, ChevronRight } from 'lucide-react';
import CaseCard from '@/components/CaseCard';

// Один блок аккордеона каталога: заголовок категории + список её кейсов.
export default function CategoryAccordion({ category, cases, expanded, onToggle, actionLabel, onCaseAction, emptyHint }) {
  const Icon = category.icon;
  return (
    <section className={`card ${expanded ? 'card-lavender' : ''}`}>
      <button className="accordion-head" onClick={onToggle} data-testid={`button-accordion-${category.key}`}>
        <span><Icon size={18} /> {category.name}</span>
        {expanded ? <ChevronDown size={17} /> : <ChevronRight size={17} />}
      </button>
      {expanded && (
        <div className="accordion-content">
          <p className="soft" style={{ fontSize: 12, margin: '0 0 5px' }}>{category.description}</p>
          {cases.length ? (
            cases.map((item) => (
              <CaseCard key={item.id} item={item} actionLabel={actionLabel} onAction={onCaseAction} />
            ))
          ) : (
            <div className="case-line">
              <span className="muted">{emptyHint || 'Пока нет кейсов в этой категории'}</span>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
