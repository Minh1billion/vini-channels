import { Menu as MenuIcon, X } from 'lucide-react';
import { useEffect, useLayoutEffect, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { FetchJobsProvider } from '@/features/fetch-jobs/FetchJobsProvider';
import { GlobalSearchProvider } from '@/features/global-search/GlobalSearchProvider';
import { VideoSimulatorProvider } from '@/features/video-simulator/VideoSimulatorProvider';
import { cn } from '@/shared/lib/cn';
import { beginNavigation } from '@/shared/lib/loadTimer';
import { BrandMark, ConfirmProvider, IconButton, LoadTimeBadge } from '@/shared/ui';
import { Sidebar } from '@/widgets/sidebar/Sidebar';
import { UtilBubble } from '@/widgets/util-bubble/UtilBubble';

export function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const location = useLocation();

  useLayoutEffect(() => {
    beginNavigation();
  }, [location.pathname]);

  useEffect(() => {
    setDrawerOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setDrawerOpen(false);
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [drawerOpen]);

  return (
    <GlobalSearchProvider>
    <ConfirmProvider>
    <FetchJobsProvider>
    <VideoSimulatorProvider>
    <div className="min-h-screen bg-bg text-fg lg:flex">
      <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-border bg-bg px-3 lg:hidden">
        <IconButton label="Mở menu" onClick={() => setDrawerOpen(true)}>
          <MenuIcon className="h-5 w-5" aria-hidden />
        </IconButton>
        <BrandMark size={26} />
        <span className="font-bold">ViniChannels</span>
      </header>

      {drawerOpen ? (
        <div
          aria-hidden
          onClick={() => setDrawerOpen(false)}
          className="fixed inset-0 z-30 animate-fade-in bg-[rgba(1,1,1,0.5)] lg:hidden"
        />
      ) : null}

      <aside
        aria-label="Thanh bên"
        className={cn(
          'fixed inset-y-0 left-0 z-40 w-[272px] border-r border-border bg-bg transition-[transform,width] duration-200 ease-out lg:sticky lg:top-0 lg:z-10 lg:h-screen lg:translate-x-0 lg:shrink-0',
          drawerOpen ? 'translate-x-0' : '-translate-x-full',
          collapsed ? 'lg:w-[72px]' : 'lg:w-[272px]',
        )}
      >
        {drawerOpen ? (
          <IconButton
            label="Đóng menu"
            onClick={() => setDrawerOpen(false)}
            className="absolute right-2 top-3 z-10 lg:hidden"
          >
            <X className="h-5 w-5" aria-hidden />
          </IconButton>
        ) : null}
        <Sidebar
          collapsed={collapsed && !drawerOpen}
          onToggleCollapsed={() => setCollapsed((value) => !value)}
          onNavigate={() => setDrawerOpen(false)}
        />
      </aside>

      <main className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-8">
        <div className="mx-auto w-full max-w-[1480px]">
          <div key={location.pathname} className="animate-rise">
            <Outlet />
          </div>
        </div>
      </main>
      <LoadTimeBadge className="fixed bottom-7 right-[5.5rem] z-40" />
      <UtilBubble />
    </div>
    </VideoSimulatorProvider>
    </FetchJobsProvider>
    </ConfirmProvider>
    </GlobalSearchProvider>
  );
}
