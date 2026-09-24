// Кабинет автора: список кейсов, публикация, приглашения.
import { useEffect, useState } from 'react';
import { useLocation } from 'wouter';
import { Copy, Pencil, Plus, Rocket, Trash2 } from 'lucide-react';
import { scenariosApi } from '@/lib/api';
import { categoryLabel } from '@/data/categories';

const statusLabels = { draft: 'Черновик', ready: 'Готов к приглашению', archived: 'Архивирован' };

export default function AdminCases({ onToast }) {
  const [, navigate] = useLocation();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState(null);

  const load = () => {
    setLoading(true);
    scenariosApi.mine().then(setItems).catch((err) => onToast?.(err.message)).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const publish = async (id) => {
    setBusyId(id);
    try {
      await scenariosApi.publish(id);
      onToast?.('Кейс опубликован, ссылка-приглашение готова');
      load();
    } catch (err) {
      onToast?.(err.message);
    } finally {
      setBusyId(null);
    }
  };

  const archive = async (id) => {
    setBusyId(id);
    try {
      await scenariosApi.archive(id);
      onToast?.('Кейс архивирован');
      load();
    } catch (err) {
      onToast?.(err.message);
    } finally {
      setBusyId(null);
    }
  };

  const remove = async (id) => {
    if (!window.confirm('Удалить кейс безвозвратно?')) return;
    setBusyId(id);
    try {
      await scenariosApi.remove(id);
      onToast?.('Кейс удалён');
      load();
    } catch (err) {
      onToast?.(err.message);
    } finally {
      setBusyId(null);
    }
  };

  const copyInvite = (item) => {
    if (!item.invite_code) return;
    const url = `${window.location.origin}/invite/${item.invite_code}`;
    navigator.clipboard?.writeText(url);
    onToast?.('Ссылка-приглашение скопирована');
  };

  return (
    <>
      <div className="page-header">
        <div>
          <span className="eyebrow">Кабинет автора</span>
          <h1 className="display">Мои кейсы.</h1>
          <p className="muted">Создавайте сценарии и делитесь ссылкой-приглашением с командой.</p>
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/admin/cases/new')} data-testid="button-new-admin-case">
          <Plus size={15} /> Новый кейс
        </button>
      </div>

      {loading ? (
        <p className="muted">Загружаем кейсы…</p>
      ) : items.length === 0 ? (
        <div className="card" style={{ padding: 24 }}>
          <p className="muted">Пока нет ни одного кейса. Создайте первый, чтобы получить ссылку-приглашение.</p>
        </div>
      ) : (
        <div className="card admin-table">
          <table>
            <thead>
              <tr><th>Название</th><th>Категория</th><th>Статус</th><th /></tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id}>
                  <td>
                    <strong>{item.name}</strong>
                    <div className="muted" style={{ fontSize: 11, marginTop: 5 }}>/{item.id}</div>
                  </td>
                  <td>{categoryLabel(item.category)}</td>
                  <td><span className={`tag ${item.status === 'archived' ? 'tag-warm' : ''}`}>{statusLabels[item.status] || item.status}</span></td>
                  <td>
                    <div style={{ display: 'flex', gap: 4, justifyContent: 'flex-end' }}>
                      {item.status === 'draft' && (
                        <button className="btn btn-quiet btn-small" disabled={busyId === item.id} onClick={() => publish(item.id)} aria-label="Опубликовать" title="Опубликовать">
                          <Rocket size={14} />
                        </button>
                      )}
                      {item.status === 'ready' && item.invite_code && (
                        <button className="btn btn-quiet btn-small" onClick={() => copyInvite(item)} aria-label="Скопировать ссылку" title="Скопировать ссылку-приглашение">
                          <Copy size={14} />
                        </button>
                      )}
                      <button className="btn btn-quiet btn-small" onClick={() => navigate(`/admin/cases/new?edit=${item.id}`)} aria-label="Редактировать" title="Редактировать">
                        <Pencil size={14} />
                      </button>
                      {item.status !== 'archived' && (
                        <button className="btn btn-quiet btn-small" disabled={busyId === item.id} onClick={() => archive(item.id)} aria-label="Архивировать" title="Архивировать">
                          <Trash2 size={14} />
                        </button>
                      )}
                      {item.status === 'archived' && (
                        <button className="btn btn-quiet btn-small" disabled={busyId === item.id} onClick={() => remove(item.id)} aria-label="Удалить" title="Удалить безвозвратно">
                          <Trash2 size={14} color="#ff9d9d" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
