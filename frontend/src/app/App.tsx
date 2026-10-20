import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { AuthProvider } from '@/features/auth/AuthProvider';
import { RequireAuth } from '@/features/auth/RequireAuth';
import { AuditPage } from '@/pages/audit/AuditPage';
import { ChannelDetailPage } from '@/pages/channel-detail/ChannelDetailPage';
import { ChannelsPage } from '@/pages/channels/ChannelsPage';
import { DashboardPage } from '@/pages/dashboard/DashboardPage';
import { LoginPage } from '@/pages/login/LoginPage';
import { UsersPage } from '@/pages/users/UsersPage';
import { VideosPage } from '@/pages/videos/VideosPage';
import { ProvidersPage } from '@/pages/providers/ProvidersPage';
import { ScoringPage } from '@/pages/scoring/ScoringPage';
import { SyncPage } from '@/pages/sync/SyncPage';
import { PartnersPage } from '@/pages/partners/PartnersPage';
import { ComparePage } from '@/pages/compare/ComparePage';
import { ReportsPage } from '@/pages/reports/ReportsPage';
import { ProfilePage } from '@/pages/profile/ProfilePage';
import { PlaceholderPage } from '@/pages/placeholder/PlaceholderPage';
import { AppLayout } from './AppLayout';
import { placeholderTitles } from './navigation';

const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    element: <RequireAuth />,
    children: [
      {
        path: '/',
        element: <AppLayout />,
        children: [
          { index: true, element: <DashboardPage /> },
          { path: 'profile', element: <ProfilePage /> },
          { path: 'partners', element: <PartnersPage /> },
          { path: 'channels', element: <ChannelsPage /> },
          { path: 'channels/:id', element: <ChannelDetailPage /> },
          { path: 'videos', element: <VideosPage /> },
          { path: 'compare', element: <ComparePage /> },
          { path: 'reports', element: <ReportsPage /> },
          { path: 'sync', element: <SyncPage /> },
          { path: 'settings/providers', element: <ProvidersPage /> },
          { path: 'settings/scoring', element: <ScoringPage /> },
          { path: 'settings/users', element: <UsersPage /> },
          { path: 'settings/audit', element: <AuditPage /> },
          ...Object.entries(placeholderTitles).map(([path, title]) => ({
            path,
            element: <PlaceholderPage title={title} />,
          })),
          { path: '*', element: <PlaceholderPage title="Không tìm thấy trang" /> },
        ],
      },
    ],
  },
]);

export function App() {
  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}
