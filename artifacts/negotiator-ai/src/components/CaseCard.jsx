import { ArrowRight } from 'lucide-react';
import { categoryLabel } from '@/data/categories';

// Карточка одного сценария (кейса) — используется в каталоге и на лендинге.
export default function CaseCard({ item, actionLabel = 'Открыть', onAction }) {
  return (
    <div className="case-line" data-testid={`case-card-${item.id}`}>
      <div>
        <strong>{item.name}</strong>
        <small>
          {categoryLabel(item.category)}
          {item.user_role ? ` · ${item.user_role}` : ''}
        </small>
        {item.description && (
          <p className="muted" style={{ fontSize: 12, margin: '6px 0 0', lineHeight: 1.5 }}>{item.description}</p>
        )}
      </div>
      <button className="btn btn-small" onClick={() => onAction?.(item)} data-testid={`button-case-action-${item.id}`}>
        {actionLabel} <ArrowRight size={13} />
      </button>
    </div>
  );
}
