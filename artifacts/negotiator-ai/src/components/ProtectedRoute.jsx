function AppContent() {
  const [user, setUser] = useState(() => readStore('negotiator-user', null));
  const [toast, setToast] = useState('');
  const setPersistedUser = (value) => { setUser(value); saveStore('negotiator-user', value); };
  const logout = () => { setUser(null); localStorage.removeItem('negotiator-user'); };
  const onToast = (text) => setToast(text);
  const privateRoute = (node, role = 'user') => user && user.role === role ? <PrivateShell user={user} onLogout={logout}>{node}</PrivateShell> : <PublicShell user={user} onLogout={logout}>
    <AuthPage mode="login" admin={role === 'admin'} onAuth={setPersistedUser} /></PublicShell>;
  return <><Switch><Route path="/login"><PublicShell user={user} onLogout={logout}><AuthPage mode="login" onAuth={setPersistedUser} /></PublicShell></Route>
  <Route path="/register"><PublicShell user={user} onLogout={logout}><AuthPage mode="register" onAuth={setPersistedUser} /></PublicShell></Route><Route path="/login/admin">
    <PublicShell user={user} onLogout={logout}><AuthPage mode="login" admin onAuth={setPersistedUser} />
  </PublicShell></Route><Route path="/register/admin"><PublicShell user={user} onLogout={logout}>
    <AuthPage mode="register" admin onAuth={setPersistedUser} /></PublicShell></Route><Route path="/onboarding">{user ? <PublicShell user={user} onLogout={logout}>
        <Onboarding onComplete={setPersistedUser} /></PublicShell> : <PublicShell user={user} onLogout={logout}><AuthPage mode="register" onAuth={setPersistedUser} /></PublicShell>}</Route>
    <Route path="/catalog"><PublicShell user={user} onLogout={logout}><div className="page container-wide"><Catalog user={user} onToast={onToast} /></div></PublicShell></Route><Route path="/"><PublicShell user={user} onLogout={logout}><Landing user={user} /></PublicShell></Route><Route path="/profile">{privateRoute(<Profile user={user} onToast={onToast} />)}</Route>
    <Route path="/constructor">{privateRoute(<ConstructorPage />)}</Route><Route path="/briefing">{privateRoute(<Briefing />)}</Route><Route path="/session">{privateRoute(<Session />)}</Route><Route path="/analytics">{privateRoute(<Analytics user={user} onUser={setPersistedUser} onToast={onToast} />)}</Route>
    <Route path="/admin/cases">{privateRoute(<AdminCases onToast={onToast} />, 'admin')}</Route><Route path="/admin/cases/new">{privateRoute(<AdminCaseNew onToast={onToast} />, 'admin')}</Route><Route component={NotFound} /></Switch>{toast && <Toast message={toast} onClose={() => setToast('')} />}</>;
}
