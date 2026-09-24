// Главный пульт управления: здесь настраивается роутинг (переключение страниц).
import { useState } from 'react';
import { Router as WouterRouter, Switch, Route, useLocation } from 'wouter';

import { useAuth } from '@/context/AuthContext';
import { ErrorBoundary } from '@/components/error-boundary';
import { PublicShell, PrivateShell } from '@/components/Shell';
import ProtectedRoute from '@/components/ProtectedRoute';
import AdminRoute from '@/components/AdminRoute';
import Toast from '@/components/Toast';

import Landing from '@/pages/Landing';
import Catalog from '@/pages/Catalog';
import Onboarding from '@/pages/Onboarding';
import Profile from '@/pages/Profile';
import ConstructorPage from '@/pages/Constructor';
import Briefing from '@/pages/Briefing';
import Session from '@/pages/Simulation';
import Analytics from '@/pages/Analytics';
import AuthPage from '@/pages/auth/Login';
import AdminCases from '@/pages/admin/MyCases';
import AdminCaseNew from '@/pages/admin/CaseConstructor';
import NotFound from '@/pages/not-found';

function AppContent() {
  const { user, logout } = useAuth();
  const [toast, setToast] = useState('');
  const onToast = (text) => setToast(text);

  return (
    <>
      <Switch>
        <Route path="/login">
          <PublicShell user={user} onLogout={logout}><AuthPage mode="login" /></PublicShell>
        </Route>
        <Route path="/register">
          <PublicShell user={user} onLogout={logout}><AuthPage mode="register" /></PublicShell>
        </Route>
        <Route path="/login/admin">
          <PublicShell user={user} onLogout={logout}><AuthPage mode="login" admin /></PublicShell>
        </Route>
        <Route path="/register/admin">
          <PublicShell user={user} onLogout={logout}><AuthPage mode="register" admin /></PublicShell>
        </Route>
        <Route path="/onboarding">
          <PublicShell user={user} onLogout={logout}><Onboarding /></PublicShell>
        </Route>
        <Route path="/catalog">
          <PublicShell user={user} onLogout={logout}>
            <div className="page container-wide"><Catalog user={user} onToast={onToast} /></div>
          </PublicShell>
        </Route>
        <Route path="/">
          <PublicShell user={user} onLogout={logout}><Landing user={user} /></PublicShell>
        </Route>
        <Route path="/profile">
          <ProtectedRoute>
            <PrivateShell user={user} onLogout={logout}><Profile user={user} onToast={onToast} /></PrivateShell>
          </ProtectedRoute>
        </Route>
        <Route path="/constructor">
          <ProtectedRoute>
            <PrivateShell user={user} onLogout={logout}><ConstructorPage /></PrivateShell>
          </ProtectedRoute>
        </Route>
        <Route path="/briefing">
          <ProtectedRoute>
            <PrivateShell user={user} onLogout={logout}><Briefing /></PrivateShell>
          </ProtectedRoute>
        </Route>
        <Route path="/session">
          <ProtectedRoute>
            <PrivateShell user={user} onLogout={logout}><Session /></PrivateShell>
          </ProtectedRoute>
        </Route>
        <Route path="/analytics">
          <ProtectedRoute>
            <PrivateShell user={user} onLogout={logout}><Analytics onToast={onToast} /></PrivateShell>
          </ProtectedRoute>
        </Route>
        <Route path="/admin/cases">
          <AdminRoute>
            <PrivateShell user={user} onLogout={logout}><AdminCases onToast={onToast} /></PrivateShell>
          </AdminRoute>
        </Route>
        <Route path="/admin/cases/new">
          <AdminRoute>
            <PrivateShell user={user} onLogout={logout}><AdminCaseNew onToast={onToast} /></PrivateShell>
          </AdminRoute>
        </Route>
        <Route component={NotFound} />
      </Switch>
      {toast && <Toast message={toast} onClose={() => setToast('')} />}
    </>
  );
}

function AppRouter() {
  const [location] = useLocation();
  return <ErrorBoundary resetKey={location}><AppContent /></ErrorBoundary>;
}

export default function App() {
  return (
    <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, '')}>
      <AppRouter />
    </WouterRouter>
  );
}
