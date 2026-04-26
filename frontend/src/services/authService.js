import api from './api';

export async function verifyAccessToken(payload) {
  const response = await api.post('/api/auth/verify-token', payload);
  return response.data;
}

export async function verifyOtp(payload) {
  const response = await api.post('/api/auth/verify-otp', payload);
  return response.data;
}

export async function exchangeFirebaseToken(payload) {
  const response = await api.post('/api/auth/firebase-login', payload);
  return response.data;
}

export async function fetchCurrentUser() {
  const response = await api.get('/api/auth/profile/');
  return response.data;
}

export async function forgotPassword(email) {
  const response = await api.post('/api/auth/forgot-password', { email });
  return response.data;
}

export async function resetPassword(payload) {
  const response = await api.post('/api/auth/reset-password', payload);
  return response.data;
}
