import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const linkBase = 'rounded-xl px-3 py-2 text-sm transition';

export default function AppLayout({ children }) {
  const { backendUser, logout } = useAuth();
  const navigate = useNavigate();

  const onLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="page-shell">
      <header className="border-b border-border bg-white">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4">
          <Link to="/dashboard" className="text-sm font-semibold tracking-tight">
            IntraDoc Intelligence
          </Link>

          <nav className="flex items-center gap-1 rounded-xl border border-border bg-soft p-1">
            <NavLink
              to="/dashboard"
              className={({ isActive }) => `${linkBase} ${isActive ? 'bg-white text-text' : 'text-gray-600 hover:text-text'}`}
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/upload"
              className={({ isActive }) => `${linkBase} ${isActive ? 'bg-white text-text' : 'text-gray-600 hover:text-text'}`}
            >
              Upload
            </NavLink>
            <NavLink
              to="/query"
              className={({ isActive }) => `${linkBase} ${isActive ? 'bg-white text-text' : 'text-gray-600 hover:text-text'}`}
            >
              Query
            </NavLink>
          </nav>

          <div className="flex items-center gap-3">
            <div className="text-right text-xs">
              <p className="font-medium text-text">{backendUser?.email || 'User'}</p>
              <p className="capitalize text-gray-500">{backendUser?.role || 'role'}</p>
            </div>
            <button className="btn-secondary py-2" onClick={onLogout}>
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl px-4 py-6">{children}</main>
    </div>
  );
}
