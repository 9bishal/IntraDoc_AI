import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return (
    <div className="page-center">
      <div className="card w-full text-center">
        <h1 className="text-xl font-semibold">Page not found</h1>
        <p className="mt-2 text-sm text-gray-500">The route does not exist.</p>
        <Link to="/dashboard" className="btn-primary mt-6 w-full">
          Go to dashboard
        </Link>
      </div>
    </div>
  );
}
