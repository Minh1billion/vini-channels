import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { BrandMark } from '@/shared/ui';
import { useAuth } from './AuthProvider';

export function RequireAuth() {
  const { status } = useAuth();
  const location = useLocation();

  if (status === 'loading') {
    return (
      <div className="grid min-h-screen place-items-center bg-bg" role="status" aria-label="Đang tải">
        <BrandMark size={40} />
      </div>
    );
  }

  if (status === 'anonymous') {
    return <Navigate to="/login" replace state={{ from: `${location.pathname}${location.search}` }} />;
  }

  return <Outlet />;
}
