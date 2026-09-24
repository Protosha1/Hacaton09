import Header from '@/components/Header';

// Обёртка для гостевых/публичных страниц (лендинг, каталог, формы входа).
export function PublicShell({ user, onLogout, children }) {
  return (
    <>
      <Header user={user} onLogout={onLogout} />
      {children}
    </>
  );
}

// Обёртка для приватных страниц — добавляет единый контейнер с отступами.
export function PrivateShell({ user, onLogout, children }) {
  return (
    <>
      <Header user={user} onLogout={onLogout} />
      <main className="page container-wide">{children}</main>
    </>
  );
}
