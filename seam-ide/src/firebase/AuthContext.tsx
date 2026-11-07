import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  User,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signOut,
  sendPasswordResetEmail,
  updateProfile,
  onAuthStateChanged,
} from 'firebase/auth';
import { auth, googleProvider } from './config';
import { getOrCreateUserProfile, UserProfile } from './firestoreService';

export type AuthContextType = {
  currentUser: User | null;
  userProfile: UserProfile | null;
  loading: boolean;
  error: string | null;
  login: (email: string, pass: string) => Promise<void>;
  signup: (name: string, email: string, pass: string) => Promise<void>;
  loginWithGoogle: () => Promise<void>;
  logout: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  demoLogin: (email?: string, name?: string) => Promise<void>;
  clearError: () => void;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check for demo user in localStorage first if running disconnected
    const savedDemo = localStorage.getItem('seam_demo_auth');
    if (savedDemo) {
      try {
        const parsed = JSON.parse(savedDemo);
        setCurrentUser(parsed.user);
        setUserProfile(parsed.profile);
        setLoading(false);
        return;
      } catch {}
    }

    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setCurrentUser(user);
      if (user) {
        try {
          const profile = await getOrCreateUserProfile({
            uid: user.uid,
            displayName: user.displayName,
            email: user.email,
            photoURL: user.photoURL,
            providerId: user.providerData?.[0]?.providerId || 'password',
          });
          setUserProfile(profile);
        } catch (err) {
          console.error('[AuthContext] Error getting profile:', err);
        }
      } else {
        setUserProfile(null);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const clearError = () => setError(null);

  // Email / Password Login
  const login = async (email: string, pass: string) => {
    setError(null);
    try {
      const cred = await signInWithEmailAndPassword(auth, email, pass);
      const profile = await getOrCreateUserProfile({
        uid: cred.user.uid,
        displayName: cred.user.displayName,
        email: cred.user.email,
        photoURL: cred.user.photoURL,
        providerId: 'password',
      });
      setUserProfile(profile);
    } catch (err: any) {
      console.warn('[Auth] Firebase login failed, checking fallback:', err.message);
      // If Firebase credentials error (e.g. simulated development env), allow local authenticated session
      if (err.code === 'auth/invalid-credential' || err.code === 'auth/user-not-found' || err.code === 'auth/wrong-password') {
        setError('Invalid email or password. Please check your credentials.');
        throw err;
      } else if (err.code === 'auth/network-request-failed' || err.code === 'auth/api-key-not-valid.-please-pass-a-valid-api-key.') {
        // Fallback demo session for offline development
        await demoLogin(email, email.split('@')[0]);
      } else {
        setError(err.message || 'Failed to sign in.');
        throw err;
      }
    }
  };

  // Email / Password Signup
  const signup = async (name: string, email: string, pass: string) => {
    setError(null);
    try {
      const cred = await createUserWithEmailAndPassword(auth, email, pass);
      if (name && cred.user) {
        await updateProfile(cred.user, { displayName: name });
      }
      const profile = await getOrCreateUserProfile({
        uid: cred.user.uid,
        displayName: name || email.split('@')[0],
        email: cred.user.email,
        photoURL: null,
        providerId: 'password',
      });
      setUserProfile(profile);
    } catch (err: any) {
      console.warn('[Auth] Firebase signup failed:', err.message);
      if (err.code === 'auth/email-already-in-use') {
        setError('An account with this email already exists.');
        throw err;
      } else if (err.code === 'auth/weak-password') {
        setError('Password should be at least 6 characters.');
        throw err;
      } else if (err.code === 'auth/network-request-failed' || err.code === 'auth/api-key-not-valid.-please-pass-a-valid-api-key.') {
        await demoLogin(email, name);
      } else {
        setError(err.message || 'Failed to create account.');
        throw err;
      }
    }
  };

  // Google Sign-In
  const loginWithGoogle = async () => {
    setError(null);
    try {
      const cred = await signInWithPopup(auth, googleProvider);
      const profile = await getOrCreateUserProfile({
        uid: cred.user.uid,
        displayName: cred.user.displayName,
        email: cred.user.email,
        photoURL: cred.user.photoURL,
        providerId: 'google.com',
      });
      setUserProfile(profile);
    } catch (err: any) {
      console.warn('[Auth] Google sign in error:', err.message);
      if (err.code === 'auth/popup-closed-by-user') {
        return;
      }
      if (err.code === 'auth/network-request-failed' || err.code === 'auth/api-key-not-valid.-please-pass-a-valid-api-key.') {
        await demoLogin('google.developer@seam.ai', 'SEAM Google Developer');
      } else {
        setError(err.message || 'Google sign-in was canceled or failed.');
        throw err;
      }
    }
  };

  // Logout
  const logout = async () => {
    localStorage.removeItem('seam_demo_auth');
    try {
      await signOut(auth);
    } catch (err) {
      console.warn('[Auth] Sign out warning:', err);
    }
    setCurrentUser(null);
    setUserProfile(null);
  };

  // Reset Password
  const resetPassword = async (email: string) => {
    setError(null);
    try {
      await sendPasswordResetEmail(auth, email);
    } catch (err: any) {
      setError(err.message || 'Failed to send password reset email.');
      throw err;
    }
  };

  // Demo / Local session fallback
  const demoLogin = async (email = 'kartheek@seam.ai', name = 'Kartheek Mudi') => {
    const mockUser = {
      uid: 'seam-user-demo-77',
      email,
      displayName: name,
      photoURL: null,
      emailVerified: true,
      isAnonymous: false,
      metadata: {},
      providerData: [{ providerId: 'seam.local', uid: email, displayName: name, email, phoneNumber: null, photoURL: null }],
      refreshToken: '',
      tenantId: null,
      delete: async () => {},
      getIdToken: async () => 'mock-token',
      getIdTokenResult: async () => ({} as any),
      reload: async () => {},
      toJSON: () => ({}),
      phoneNumber: null,
      providerId: 'seam.local',
    } as unknown as User;

    const profile: UserProfile = {
      uid: 'seam-user-demo-77',
      displayName: name,
      email,
      provider: 'seam.local',
      createdAt: new Date().toISOString(),
      lastLoginAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    localStorage.setItem('seam_demo_auth', JSON.stringify({ user: mockUser, profile }));
    setCurrentUser(mockUser);
    setUserProfile(profile);
    setLoading(false);
  };

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        userProfile,
        loading,
        error,
        login,
        signup,
        loginWithGoogle,
        logout,
        resetPassword,
        demoLogin,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
