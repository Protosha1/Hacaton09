import { Redirect } from 'wouter';
import { useAuth } from '@/context/AuthContext';

// Пускает дальше только вошедших пользователей с role="user".
// Админов отправляет в их кабинет, гостей — на страницу входа.
export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Redirect to="/login" />;
  if (user.role === 'admin') return <Redirect to="/admin/cases" />;
  if (user.status === 'pending_onboarding') return <Redirect to="/onboarding" />;
  return children;
}
