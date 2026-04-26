import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { logError, logInfo } from '../utils/logger';

export default function ForgotPasswordPage() {
  const { sendReset, performReset } = useAuth();
  const navigate = useNavigate();
  
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [step, setStep] = useState(1); // 1: Email, 2: OTP & Password
  
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSendOTP = async (event) => {
    event.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    try {
      await sendReset(email);
      logInfo('OTP request sent for:', email);
      setMessage('OTP has been sent to your email.');
      setStep(2);
    } catch (err) {
      logError('Forgot password error:', err);
      setError(err?.response?.data?.error || 'Could not send OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (event) => {
    event.preventDefault();
    setLoading(true);
    setMessage('');
    setError('');

    try {
      await performReset({ email, otp, new_password: newPassword });
      logInfo('Password reset success for:', email);
      setMessage('Password reset successfully! Redirecting to login...');
      setTimeout(() => navigate('/login'), 3000);
    } catch (err) {
      logError('Reset password error:', err);
      setError(err?.response?.data?.error || 'Invalid OTP or reset failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-center">
      <div className="card w-full max-w-md">
        <h1 className="text-xl font-semibold">
          {step === 1 ? 'Forgot password' : 'Reset password'}
        </h1>
        <p className="mt-2 text-sm text-gray-500">
          {step === 1 
            ? 'Enter your email to receive a 6-digit verification code.' 
            : `Enter the code sent to ${email} and your new password.`}
        </p>

        {step === 1 ? (
          <form onSubmit={handleSendOTP} className="mt-6 space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium">Email</label>
              <input 
                className="input" 
                type="email" 
                required 
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                placeholder="Enter your registered email"
              />
            </div>

            {error ? <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-600 border border-red-100">{error}</p> : null}
            {message ? <p className="rounded-xl bg-indigo-50 px-3 py-2 text-sm text-indigo-700 border border-indigo-100">{message}</p> : null}

            <button className="btn-primary w-full py-3" type="submit" disabled={loading}>
              {loading ? 'Sending OTP...' : 'Send OTP'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleResetPassword} className="mt-6 space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium">6-Digit OTP</label>
              <input 
                className="input text-center text-2xl tracking-[10px] font-mono" 
                type="text" 
                maxLength="6"
                required 
                value={otp} 
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))} 
                placeholder="000000"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium">New Password</label>
              <input 
                className="input" 
                type="password" 
                required 
                value={newPassword} 
                onChange={(e) => setNewPassword(e.target.value)} 
                placeholder="Minimum 8 characters"
                minLength="8"
              />
            </div>

            {error ? <p className="rounded-xl bg-red-50 px-3 py-2 text-sm text-red-600 border border-red-100">{error}</p> : null}
            {message ? <p className="rounded-xl bg-green-50 px-3 py-2 text-sm text-green-700 border border-green-100">{message}</p> : null}

            <button className="btn-primary w-full py-3" type="submit" disabled={loading}>
              {loading ? 'Resetting...' : 'Reset Password'}
            </button>

            <button 
              type="button" 
              onClick={() => setStep(1)} 
              className="w-full text-sm text-indigo-600 hover:text-indigo-800"
              disabled={loading}
            >
              Back to email entry
            </button>
          </form>
        )}

        <div className="mt-5 text-sm text-gray-600">
          <Link to="/login" className="text-text">Back to login</Link>
        </div>
      </div>
    </div>
  );
}
