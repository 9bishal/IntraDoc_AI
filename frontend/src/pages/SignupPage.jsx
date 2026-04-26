import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { verifyAccessToken } from '../services/authService';
import { logError, logInfo } from '../utils/logger';
import { fetchSignInMethodsForEmail } from 'firebase/auth';
import { firebaseAuth } from '../firebase';

export default function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ email: '', password: '', accessToken: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      logInfo('Verifying pre-signup token...');
      logInfo('Access token used for signup:', form.accessToken);
      
      // 1. Always verify the backend access token first (RBAC check)
      await verifyAccessToken({
        email: form.email,
        access_token: form.accessToken,
      });

      logInfo('Token verified. Checking account status...');
      
      try {
        // 2. Try to create the Firebase account
        await signup({ email: form.email, password: form.password });
        logInfo('New Firebase account created.');
      } catch (fbErr) {
        // 3. If account exists in Firebase, that's fine - we just continue to link it to Django
        if (fbErr.code === 'auth/email-already-in-use') {
          logInfo('User already exists in Firebase. Proceeding to link with Django...');
        } else {
          throw fbErr; // Rethrow other Firebase errors
        }
      }

      // 4. Move to OTP verification to finalize the Django link
      navigate('/verify-otp', {
        replace: true,
        state: { email: form.email },
      });
    } catch (err) {
      logError('Signup flow error:', err);
      const apiMessage = err?.response?.data?.error || err?.response?.data?.detail;
      const firebaseCode = err?.code || '';
      const statusCode = err?.response?.status;
      const rawData =
        typeof err?.response?.data === 'string'
          ? err.response.data
          : JSON.stringify(err?.response?.data || {});

      logError('Signup debug details:', {
        statusCode,
        firebaseCode,
        message: err?.message,
        response: err?.response?.data,
        accessToken: form.accessToken,
      });

      if (firebaseCode === 'auth/email-already-in-use') {
        setError('This email is already registered. Please sign in instead.');
      } else if (firebaseCode === 'auth/invalid-api-key') {
        setError('Firebase is not configured correctly. Contact admin.');
      } else if (apiMessage) {
        setError(apiMessage);
      } else if (statusCode) {
        setError(`Signup failed (${statusCode}): ${err?.message || rawData}`);
      } else {
        setError(
          'Signup failed. If token verification already succeeded once, the one-time token is now consumed. Ask admin for a new token.'
        );
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-center">
      <div className="card w-full">
        <h1 className="text-xl font-semibold">Create account</h1>
        <p className="mt-2 text-sm text-gray-500">Signup is token-gated by admin-issued access token.</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Email</label>
            <input className="input" type="email" required value={form.email} onChange={(e) => handleChange('email', e.target.value)} />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">Password</label>
            <input className="input" type="password" required value={form.password} onChange={(e) => handleChange('password', e.target.value)} minLength={8} />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">Access Token</label>
            <input className="input" type="text" required value={form.accessToken} onChange={(e) => handleChange('accessToken', e.target.value)} />
          </div>

          {error ? <p className="rounded-xl bg-soft px-3 py-2 text-sm text-gray-700">{error}</p> : null}

          <button className="btn-primary w-full" type="submit" disabled={loading}>
            {loading ? 'Creating account...' : 'Verify token and signup'}
          </button>
        </form>

        <div className="mt-5 text-sm text-gray-600">
          Already registered? <Link className="text-text" to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
