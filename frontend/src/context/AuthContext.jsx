import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import {
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signOut,
} from 'firebase/auth';
import { firebaseAuth, firebaseConfigError, trackEvent } from '../firebase';
import { exchangeFirebaseToken, fetchCurrentUser, forgotPassword, resetPassword } from '../services/authService';
import { getAccessibleDepartments, normalizeRole } from '../utils/roles';
import { logError, logInfo } from '../utils/logger';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [firebaseUser, setFirebaseUser] = useState(null);
  const [backendToken, setBackendToken] = useState(localStorage.getItem('backend_access_token'));
  const [backendUser, setBackendUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const clearAuthState = () => {
    localStorage.removeItem('backend_access_token');
    localStorage.removeItem('backend_refresh_token');
    localStorage.removeItem('firebase_uid');
    setBackendToken(null);
    setBackendUser(null);
  };

  const syncBackendSession = async (user) => {
    const idToken = await user.getIdToken(true);
    logInfo('Auth flow: exchanging Firebase token with backend');

    const session = await exchangeFirebaseToken({
      firebase_token: idToken,
      email: user.email,
      uid: user.uid,
    });

    const accessToken = session?.access || session?.token || session?.jwt;
    if (!accessToken) {
      throw new Error('Backend JWT not provided by /api/auth/firebase-login');
    }

    localStorage.setItem('backend_access_token', accessToken);
    if (session?.refresh) {
      localStorage.setItem('backend_refresh_token', session.refresh);
    }
    localStorage.setItem('firebase_uid', user.uid);
    setBackendToken(accessToken);

    const profile = await fetchCurrentUser();
    const normalizedRole = normalizeRole(profile?.role || profile?.user?.role);

    const mergedUser = {
      ...profile,
      email: profile?.email || user.email,
      role: normalizedRole,
      departments: getAccessibleDepartments(normalizedRole),
    };

    logInfo('Role fetching success:', mergedUser);
    setBackendUser(mergedUser);
  };

  useEffect(() => {
    if (!firebaseAuth) {
      logError('Authentication disabled:', firebaseConfigError);
      setLoading(false);
      return undefined;
    }

    const unsubscribe = onAuthStateChanged(firebaseAuth, async (user) => {
      setFirebaseUser(user);

      if (!user) {
        clearAuthState();
        setLoading(false);
        return;
      }

      try {
        const storedUid = localStorage.getItem('firebase_uid');
        if (!backendToken || storedUid !== user.uid) {
          await syncBackendSession(user);
        } else if (!backendUser) {
          const profile = await fetchCurrentUser();
          const normalizedRole = normalizeRole(profile?.role || profile?.user?.role);
          setBackendUser({
            ...profile,
            email: profile?.email || user.email,
            role: normalizedRole,
            departments: getAccessibleDepartments(normalizedRole),
          });
        }

        logInfo('Login success:', {
          uid: user.uid,
          email: user.email,
        });
      } catch (error) {
        logError('Authentication flow error:', error);
        clearAuthState();
        try {
          await signOut(firebaseAuth);
        } catch (signOutError) {
          logError('Forced logout after auth failure:', signOutError);
        }
      } finally {
        setLoading(false);
      }
    });

    return unsubscribe;
  }, []);

  const login = async ({ email, password }) => {
    if (!firebaseAuth) {
      throw new Error(firebaseConfigError || 'Firebase is not configured');
    }
    setLoading(true);
    try {
      const credential = await signInWithEmailAndPassword(firebaseAuth, email, password);
      await syncBackendSession(credential.user);
      trackEvent('login', { method: 'email' });
      return credential.user;
    } finally {
      setLoading(false);
    }
  };

  const signup = async ({ email, password }) => {
    if (!firebaseAuth) {
      throw new Error(firebaseConfigError || 'Firebase is not configured');
    }
    setLoading(true);
    try {
      const credential = await createUserWithEmailAndPassword(firebaseAuth, email, password);
      logInfo('Signup success (Firebase):', { uid: credential.user.uid, email: credential.user.email });
      trackEvent('sign_up', { method: 'email' });
      return credential.user;
    } finally {
      setLoading(false);
    }
  };

  const sendReset = async (email) => {
    logInfo('Forgot password request (Backend):', email);
    await forgotPassword(email);
  };

  const performReset = async (payload) => {
    logInfo('Reset password request (Backend):', payload.email);
    await resetPassword(payload);
  };

  const logout = async () => {
    if (!firebaseAuth) {
      clearAuthState();
      return;
    }
    await signOut(firebaseAuth);
    clearAuthState();
    logInfo('Logout success');
    trackEvent('logout');
  };
  const value = useMemo(
    () => ({
      firebaseUser,
      backendUser,
      backendToken,
      loading,
      isAuthenticated: Boolean(firebaseUser && backendToken),
      login,
      signup,
      sendReset,
      performReset,
      logout,
      refreshProfile: async () => {
        const profile = await fetchCurrentUser();
        const normalizedRole = normalizeRole(profile?.role || profile?.user?.role);
        const mergedUser = {
          ...profile,
          role: normalizedRole,
          departments: getAccessibleDepartments(normalizedRole),
        };
        setBackendUser(mergedUser);
        return mergedUser;
      },
      configError: firebaseConfigError,
    }),
    [firebaseUser, backendUser, backendToken, loading]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
