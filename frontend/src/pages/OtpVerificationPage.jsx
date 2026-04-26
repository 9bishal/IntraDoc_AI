import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { verifyOtp } from '../services/authService';
import { logError, logInfo } from '../utils/logger';

export default function OtpVerificationPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState(location.state?.email || '');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await verifyOtp({ email, otp });
      logInfo('OTP verification success:', email);
      setSuccess('Email verified successfully. You can now sign in.');
      setTimeout(() => navigate('/login', { replace: true }), 800);
    } catch (err) {
      logError('OTP verification failed:', err);
      const apiMessage = err?.response?.data?.error || err?.response?.data?.detail;
      setError(apiMessage || 'Invalid OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-center">
      <div className="card w-full">
        <h1 className="text-xl font-semibold">Verify OTP</h1>
        <p className="mt-2 text-sm text-gray-500">Enter the OTP sent by backend email service.</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">Email</label>
            <input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">OTP</label>
            <input className="input" type="text" required value={otp} onChange={(e) => setOtp(e.target.value)} />
          </div>

          {error ? <p className="rounded-xl bg-soft px-3 py-2 text-sm text-gray-700">{error}</p> : null}
          {success ? <p className="rounded-xl bg-soft px-3 py-2 text-sm text-gray-700">{success}</p> : null}

          <button className="btn-primary w-full" type="submit" disabled={loading}>
            {loading ? 'Verifying...' : 'Verify OTP'}
          </button>
        </form>

        <div className="mt-5 text-sm text-gray-600">
          <Link className="text-text" to="/login">Back to login</Link>
        </div>
      </div>
    </div>
  );
}
