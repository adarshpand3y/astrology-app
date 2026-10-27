import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { tokenStore } from '../api/client';
import { authApi } from '../api/endpoints';
import { invalidateAll } from '../hooks/useApi';
import { network } from '../network';

// The last /auth/me, so an offline launch still knows the active chart and place.
const USER_KEY = 'auth.user';
const loadSavedUser = () => AsyncStorage.getItem(USER_KEY).then((raw) => (raw ? JSON.parse(raw) : null)).catch(() => null);

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [status, setStatus] = useState('loading'); // loading | signedIn | signedOut
  const [user, setUserState] = useState(null);

  const setUser = useCallback((u) => {
    setUserState(u);
    (u ? AsyncStorage.setItem(USER_KEY, JSON.stringify(u)) : AsyncStorage.removeItem(USER_KEY)).catch(() => {});
  }, []);

  const signOutLocal = useCallback(async () => {
    await tokenStore.clear();
    invalidateAll();
    setUser(null);
    setStatus('signedOut');
  }, [setUser]);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const { access, refresh } = await tokenStore.load();
        if (!access && !refresh) { if (alive) setStatus('signedOut'); return; }
        // Known offline: don't wait for the request to time out, open with the saved account.
        if (!(await network.check())) {
          const saved = await loadSavedUser();
          if (alive) { setUserState(saved); setStatus('signedIn'); }
          return;
        }
        const me = await authApi.me();
        if (alive) { setUser(me); setStatus('signedIn'); }
      } catch (e) {
        // Keep the session on network errors so offline launches still work, and when the
        // build is too old (the update screen covers the app; the session survives the update).
        if (!alive) return;
        if (['network_error', 'timeout', 'update_required'].includes(e.code)) {
          setUserState(await loadSavedUser());
          setStatus('signedIn');
        }
        else await signOutLocal();
      }
    })();
    const off = tokenStore.onForcedLogout(() => { setUser(null); setStatus('signedOut'); invalidateAll(); });
    return () => { alive = false; off(); };
  }, [signOutLocal, setUser]);

  const acceptTokens = useCallback(async (data) => {
    await tokenStore.set(data);
    setUser(data.user ?? (await authApi.me()));
    setStatus('signedIn');
  }, [setUser]);

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
  }), [status, user, setUser, acceptTokens, signOutLocal]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}
