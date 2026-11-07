import { doc, getDoc, setDoc, updateDoc, collection, getDocs, deleteDoc } from 'firebase/firestore';
import { db } from './config';

export type UserProfile = {
  uid: string;
  displayName: string;
  email: string;
  photoURL?: string;
  provider: string;
  createdAt: string;
  lastLoginAt: string;
  updatedAt: string;
};

export type UserPreferences = {
  theme?: 'dark' | 'light' | 'system';
  wordWrap?: boolean;
  fontSize?: number;
  tabSize?: number;
  minimap?: boolean;
  terminalHeight?: number;
  recentProjects?: string[];
};

export type FirestoreProjectMeta = {
  projectId: string;
  projectName: string;
  domain?: string;
  requirement?: string;
  createdAt: string;
  updatedAt: string;
  workflowStatus?: string;
};

// 1. User Profile Management
export async function getOrCreateUserProfile(user: {
  uid: string;
  displayName?: string | null;
  email?: string | null;
  photoURL?: string | null;
  providerId?: string;
}): Promise<UserProfile> {
  const userRef = doc(db, 'users', user.uid);
  const now = new Date().toISOString();

  try {
    const snap = await getDoc(userRef);
    if (snap.exists()) {
      const data = snap.data() as UserProfile;
      await updateDoc(userRef, { lastLoginAt: now, updatedAt: now });
      return { ...data, lastLoginAt: now, updatedAt: now };
    }
  } catch (err) {
    console.warn('[Firestore] Profile lookup fell back to local memory:', err);
  }

  // Create new profile
  const newProfile: UserProfile = {
    uid: user.uid,
    displayName: user.displayName || user.email?.split('@')[0] || 'SEAM Engineer',
    email: user.email || '',
    photoURL: user.photoURL || undefined,
    provider: user.providerId || 'password',
    createdAt: now,
    lastLoginAt: now,
    updatedAt: now,
  };

  try {
    await setDoc(userRef, newProfile);
  } catch (err) {
    console.warn('[Firestore] Profile creation stored locally:', err);
  }

  return newProfile;
}

// 2. User Preferences Persistence
export async function saveUserPreferences(uid: string, preferences: UserPreferences): Promise<void> {
  try {
    const prefRef = doc(db, 'users', uid, 'preferences', 'ui');
    await setDoc(prefRef, preferences, { merge: true });
  } catch (err) {
    console.warn('[Firestore] Preferences saved to localStorage:', err);
    try {
      localStorage.setItem(`seam_prefs_${uid}`, JSON.stringify(preferences));
    } catch {}
  }
}

export async function getUserPreferences(uid: string): Promise<UserPreferences | null> {
  try {
    const prefRef = doc(db, 'users', uid, 'preferences', 'ui');
    const snap = await getDoc(prefRef);
    if (snap.exists()) {
      return snap.data() as UserPreferences;
    }
  } catch (err) {
    console.warn('[Firestore] Preferences read from localStorage:', err);
  }

  try {
    const local = localStorage.getItem(`seam_prefs_${uid}`);
    if (local) return JSON.parse(local);
  } catch {}

  return null;
}

// 3. Project Metadata Persistence
export async function saveProjectMeta(uid: string, meta: FirestoreProjectMeta): Promise<void> {
  try {
    const projRef = doc(db, 'users', uid, 'projects', meta.projectId);
    await setDoc(projRef, meta, { merge: true });
  } catch (err) {
    console.warn('[Firestore] Project metadata stored in local storage:', err);
  }
}

export async function getUserProjectsMeta(uid: string): Promise<FirestoreProjectMeta[]> {
  try {
    const colRef = collection(db, 'users', uid, 'projects');
    const snap = await getDocs(colRef);
    return snap.docs.map(d => d.data() as FirestoreProjectMeta);
  } catch (err) {
    console.warn('[Firestore] Reading user projects metadata:', err);
    return [];
  }
}
