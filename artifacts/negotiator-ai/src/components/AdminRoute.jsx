import { Redirect } from 'wouter';
import { useAuth } from '@/context/AuthContext';

// Пускает дальше только вошедших администраторов (role="admin").
export default function AdminRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Redirect to="/login/admin" />;
  if (user.role !== 'admin') return <Redirect to="/profile" />;
  return children;
}
