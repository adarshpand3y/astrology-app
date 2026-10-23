import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { tokenStore } from '../api/client';
import { authApi } from '../api/endpoints';
import { invalidateAll } from '../hooks/useApi';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [status, setStatus] = useState('loading'); // loading | signedIn | signedOut
  const [user, setUser] = useState(null);

  const signOutLocal = useCallback(async () => {
    await tokenStore.clear();
    invalidateAll();
    setUser(null);
    setStatus('signedOut');
  }, []);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const { access, refresh } = await tokenStore.load();
        if (!access && !refresh) { if (alive) setStatus('signedOut'); return; }
        const me = await authApi.me();
        if (alive) { setUser(me); setStatus('signedIn'); }
      } catch (e) {
        // Keep the session on network errors so offline launches still work.
        if (!alive) return;
        if (e.code === 'network_error' || e.code === 'timeout') setStatus('signedIn');
        else await signOutLocal();
      }
    })();
    const off = tokenStore.onForcedLogout(() => { setUser(null); setStatus('signedOut'); invalidateAll(); });
    return () => { alive = false; off(); };
  }, [signOutLocal]);

  const acceptTokens = useCallback(async (data) => {
    await tokenStore.set(data);
    setUser(data.user ?? (await authApi.me()));
    setStatus('signedIn');
  }, []);

  const value = useMemo(() => ({
    status,
    user,
    setUser,
    signIn: async (email, password) => acceptTokens(await authApi.login(email.trim().toLowerCase(), password)),
    verifyEmail: async (email, code) => acceptTokens(await authApi.verifyEmail(email.trim().toLowerCase(), code)),
    acceptTokens,
    /** PATCH /auth/me (current place, active profile, name) and keep the user in sync. */
    updateMe: async (patch) => {
      const u = await authApi.updateMe(patch);
      setUser(u);
      return u;
    },
    refreshUser: async () => {
      const u = await authApi.me();
      setUser(u);
      return u;
    },
    signOut: async () => {
      const { refresh } = tokenStore.get();
      try { if (refresh) await authApi.logout(refresh); } catch { /* best effort */ }
      await signOutLocal();
    },
    signOutLocal,
  }), [status, user, acceptTokens, signOutLocal]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
