import { useEffect } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import ProtectedRoute from '../components/ProtectedRoute';
import LoginPage from '../pages/LoginPage';
import SignupPage from '../pages/SignupPage';
import ForgotPasswordPage from '../pages/ForgotPasswordPage';
import OtpVerificationPage from '../pages/OtpVerificationPage';
import DashboardPage from '../pages/DashboardPage';
import UploadPage from '../pages/UploadPage';
import QueryPage from '../pages/QueryPage';
import NotFoundPage from '../pages/NotFoundPage';

function HomeRedirect() {
  const lastPath = localStorage.getItem('last_path');
  const path = lastPath && !['/login', '/signup', '/forgot-password', '/verify-otp'].includes(lastPath) 
    ? lastPath 
    : "/dashboard";
  return <Navigate to={path} replace />;
}

export default function AppRoutes() {
  const location = useLocation();

  useEffect(() => {
    const publicPaths = ['/login', '/signup', '/forgot-password', '/verify-otp', '/'];
    if (!publicPaths.includes(location.pathname)) {
      localStorage.setItem('last_path', location.pathname);
    }
  }, [location.pathname]);

  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/verify-otp" element={<OtpVerificationPage />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/query" element={<QueryPage />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
