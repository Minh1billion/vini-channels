import { Activity, Clapperboard, Smartphone, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useFetchJobs } from '@/features/fetch-jobs/FetchJobsProvider';
import { useVideoSimulator } from '@/features/video-simulator/VideoSimulatorProvider';
import { cn } from '@/shared/lib/cn';
import { IconButton, Tabs } from '@/shared/ui';
import { FetchJobsList } from '@/widgets/fetch-dock/FetchJobsList';
import { SimulatorPane } from './SimulatorPane';

type PaneId = 'simulator' | 'jobs';

export function UtilBubble() {
  const { jobs } = useFetchJobs();
  const { openSignal } = useVideoSimulator();
  const [open, setOpen] = useState(false);
  const [pane, setPane] = useState<PaneId>('simulator');

  const running = jobs.filter((job) => job.status === 'running').length;
  const failed = jobs.some((job) => job.status === 'failed');

  useEffect(() => {
    if (openSignal === 0) return;
    setPane('simulator');
    setOpen(true);
  }, [openSignal]);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open]);

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col items-end gap-3"
    >
      {open ? (
        <section
          aria-label="Tiện ích"
          className="relative w-[min(360px,calc(100vw-2rem))] animate-pop-in-up overflow-hidden rounded-card border border-border bg-card shadow-pop"
        >
          <div className="flex items-center gap-2 border-b border-border px-3">
            <div className="flex-1 [&>div]:border-b-0">
              <Tabs
                label="Tiện ích"
                fill
                value={pane}
                onChange={setPane}
                tabs={[
                  { id: 'simulator', label: 'Xem trước', icon: Smartphone },
                  { id: 'jobs', label: running > 0 ? `Tiến trình (${running})` : 'Tiến trình', icon: Activity },
                ]}
              />
            </div>
            <IconButton label="Thu gọn" size="sm" onClick={() => setOpen(false)}>
              <X className="h-4 w-4" aria-hidden />
            </IconButton>
          </div>

          <div className="h-[calc(min(52vh,480px)+10.5rem)] overflow-y-auto">
            {pane === 'simulator' ? (
              <div key="simulator" role="tabpanel" id="panel-simulator" aria-labelledby="tab-simulator" className="h-full animate-fade-in">
                <SimulatorPane />
              </div>
            ) : (
              <div key="jobs" role="tabpanel" id="panel-jobs" aria-labelledby="tab-jobs" className="h-full animate-fade-in">
                <FetchJobsList />
              </div>
            )}
          </div>

          {running > 0 && pane === 'simulator' ? (
            <button
              type="button"
              onClick={() => setPane('jobs')}
              className="flex w-full items-center gap-2 border-t border-border px-3 py-2 text-left text-xs text-muted transition-colors hover:bg-surface"
            >
              <span className="h-2 w-2 animate-pulse rounded-full bg-blue" aria-hidden />
              Đang lấy dữ liệu ({running}), bấm để xem
            </button>
          ) : null}
        </section>
      ) : null}

      <button
        type="button"
        aria-label={open ? 'Đóng tiện ích' : 'Mở tiện ích: xem trước TikTok và tiến trình'}
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
        className={cn(
          'relative flex h-14 w-14 items-center justify-center rounded-full bg-ink text-paper shadow-pop transition-transform duration-200 ease-out hover:scale-105 active:scale-95',
          running > 0 && 'ring-2 ring-blue',
        )}
      >
        <Clapperboard className="h-6 w-6" aria-hidden />
        {running > 0 ? (
          <span className="absolute -right-1.5 -top-1.5 flex h-6 min-w-6 items-center justify-center rounded-full border-2 border-red bg-blue px-1 text-[11px] font-extrabold text-on-blue">
            {running}
          </span>
        ) : failed ? (
          <span className="absolute right-0 top-0 h-3 w-3 rounded-full border-2 border-bg bg-red" aria-hidden />
        ) : null}
      </button>
    </div>
  );
}
