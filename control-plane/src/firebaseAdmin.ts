import { applicationDefault, cert, getApps, initializeApp } from "firebase-admin/app";

export function initFirebaseAdmin(): void {
  if (getApps().length) {
    return;
  }
  const raw = process.env.FIREBASE_SERVICE_ACCOUNT_JSON;
  if (raw) {
    initializeApp({ credential: cert(JSON.parse(raw)) });
    return;
  }
  initializeApp({ credential: applicationDefault() });
}
