import { initializeApp, getApps, FirebaseApp } from 'firebase/app';
import {
  getAuth,
  GoogleAuthProvider,
  Auth,
} from 'firebase/auth';
import { getFirestore, Firestore } from 'firebase/firestore';

// Client-side Firebase configuration
// Defaults fall back to SEAM development project credentials if environment variables are not supplied
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || 'AIzaSyDemoSEAMFrameworkKeyForLocalDev77',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || 'seam-framework-sdlc.firebaseapp.com',
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || 'seam-framework-sdlc',
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || 'seam-framework-sdlc.appspot.com',
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '772910384729',
  appId: import.meta.env.VITE_FIREBASE_APP_ID || '1:772910384729:web:91823746a5b6c7d8e9f0',
};

let app: FirebaseApp;
let auth: Auth;
let db: Firestore;
let isConfigured = false;

try {
  if (!getApps().length) {
    app = initializeApp(firebaseConfig);
  } else {
    app = getApps()[0];
  }
  auth = getAuth(app);
  db = getFirestore(app);
  isConfigured = true;
} catch (err) {
  console.warn('[SEAM Firebase] Initialized with local fallback context:', err);
  // Re-initialize with placeholder if needed
  app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig, 'seam-fallback');
  auth = getAuth(app);
  db = getFirestore(app);
}

const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({ prompt: 'select_account' });

export { app, auth, db, googleProvider, isConfigured };
