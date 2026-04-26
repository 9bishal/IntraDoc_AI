import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { logError, logInfo } from '../utils/logger';

export default function LoginPage() {
  const { login, loading, configError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const from = location.state?.from || '/dashboard';

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');

    try {
      const user = await login({ email, password });
      logInfo('Login success:', user?.email);
      navigate(from, { replace: true });
    } catch (err) {
      logError('Login failed:', err);
      setError('Login failed. Check your credentials and try again.');
    }
  };

  return (
    <div className="page-center">
      <div className="card w-full">
        <h1 className="text-xl font-semibold">Sign in</h1>
        <p className="mt-2 text-sm text-gray-500">Use your employee email and password.</p>
        {configError ? (
          <p className="mt-3 rounded-xl bg-soft px-3 py-2 text-sm text-gray-700">
            Firebase setup issue: {configError}. Add valid Firebase values in `frontend/.env`, then restart Vite.
          </p>
        ) : null}

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Email</label>
            <input className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">Password</label>
            <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>

          {error ? <p className="rounded-xl bg-soft px-3 py-2 text-sm text-gray-700">{error}</p> : null}

          <button className="btn-primary w-full" type="submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <div className="mt-5 flex items-center justify-between text-sm">
          <Link className="text-gray-600 hover:text-text" to="/signup">
            Create account
          </Link>
          <Link className="text-gray-600 hover:text-text" to="/forgot-password">
            Forgot password?
          </Link>
        </div>
      </div>
    </div>
  );
}
