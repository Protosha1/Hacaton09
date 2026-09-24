import { Link } from 'wouter';

export default function NotFound() {
  return (
    <div className="page container-wide" style={{ textAlign: 'center', padding: '80px 20px' }}>
      <span className="eyebrow">404</span>
      <h1 className="display" style={{ margin: '14px 0' }}>Такой страницы нет.</h1>
      <p className="muted" style={{ marginBottom: 24 }}>Возможно, ссылка устарела или адрес введён неверно.</p>
      <Link href="/" className="btn btn-primary">На главную</Link>
    </div>
  );
}
