import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getAnalytics, logEvent, isSupported } from 'firebase/analytics';
import { getFirestore, collection, addDoc } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID, // Useful for Analytics
};

const requiredKeys = [
  'apiKey',
  'authDomain',
  'projectId',
  'storageBucket',
  'messagingSenderId',
  'appId',
];

const missingKeys = requiredKeys.filter((key) => !firebaseConfig[key]);
export let firebaseConfigError = null;
export let firebaseAuth = null;
export let analytics = null;
export let db = null;

if (missingKeys.length > 0) {
  firebaseConfigError = `Missing Firebase env variables: ${missingKeys.join(', ')}`;
  console.error('Firebase config error:', firebaseConfigError);
} else {
  try {
    const app = initializeApp(firebaseConfig);
    firebaseAuth = getAuth(app);
    db = getFirestore(app);
    
    // Initialize Analytics
    isSupported().then((supported) => {
      if (supported) {
        analytics = getAnalytics(app);
      }
    });
  } catch (error) {
    firebaseConfigError = error?.message || 'Failed to initialize Firebase';
    console.error('Firebase initialization error:', error);
  }
}

export const trackEvent = async (eventName, eventParams = {}) => {
  // 1. Log to Google Analytics
  if (analytics) {
    try {
      logEvent(analytics, eventName, eventParams);
    } catch (e) {
      console.warn('Failed to log event to Analytics', e);
    }
  }

  // 2. Store every event permanently in Firebase Firestore Datastore
  if (db) {
    try {
      const user = firebaseAuth?.currentUser;
      await addDoc(collection(db, 'user_activity_logs'), {
        event_name: eventName,
        ...eventParams,
        user_uid: user?.uid || null,
        user_email: user?.email || null,
        server_timestamp: new Date().toISOString(),
      });
    } catch (e) {
      console.warn('Failed to store event in Firestore Datastore', e);
    }
  }
};

// --- CHAT HISTORY STORAGE (FIRESTORE) ---

import { doc, getDoc, setDoc } from 'firebase/firestore';

export const getChatHistory = async (department) => {
  if (!db || !firebaseAuth?.currentUser || !department) return [];
  
  const uid = firebaseAuth.currentUser.uid;
  const docRef = doc(db, 'chat_history', uid);
  
  try {
    const docSnap = await getDoc(docRef);
    if (docSnap.exists()) {
      const data = docSnap.data();
      const deptKey = department.toUpperCase();
      return data[deptKey] || [];
    }
  } catch (error) {
    console.error('Error fetching chat history from Firestore:', error);
  }
  return [];
};

export const appendChatHistory = async (department, messagesToAdd) => {
  if (!db || !firebaseAuth?.currentUser || !department || !messagesToAdd.length) return;
  
  const uid = firebaseAuth.currentUser.uid;
  const docRef = doc(db, 'chat_history', uid);
  const deptKey = department.toUpperCase();
  
  try {
    const docSnap = await getDoc(docRef);
    let currentHistory = [];
    
    if (docSnap.exists()) {
      currentHistory = docSnap.data()[deptKey] || [];
    }
    
    // Append new messages
    const updatedHistory = [...currentHistory, ...messagesToAdd];
    
    // Write back
    await setDoc(docRef, {
      [deptKey]: updatedHistory
    }, { merge: true });
    
  } catch (error) {
    console.error('Error appending chat history to Firestore:', error);
  }
};

