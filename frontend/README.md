# IntraDoc Frontend (React + Vite)

Production-oriented frontend for a RAG document intelligence system.

## Stack
- React (Vite)
- React Router
- Axios
- Firebase Authentication (email/password + forgot password)
- Tailwind CSS

## Setup
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Required Environment Variables
- `VITE_API_BASE_URL`
- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_STORAGE_BUCKET`
- `VITE_FIREBASE_MESSAGING_SENDER_ID`
- `VITE_FIREBASE_APP_ID`

## Auth Flow
1. Signup requires backend token verification (`POST /api/auth/verify-token`).
2. Firebase account is created only after token validation.
3. OTP verification is handled by backend (`POST /api/auth/verify-otp`).
4. Login uses Firebase email/password.
5. Firebase token is exchanged for backend JWT (`POST /api/auth/firebase-login`).
6. Role/profile fetched from backend (`GET /api/auth/profile/`).

## Backend Endpoints Expected
- `POST /api/auth/verify-token`
- `POST /api/auth/verify-otp`
- `POST /api/auth/firebase-login`
- `GET /api/auth/profile/`
- `POST /api/documents/upload/`
- `POST /api/chat/`
