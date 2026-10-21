import { CheckCircle2, ChevronDown, ChevronUp, Loader2, X, XCircle } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { FetchJobRecord } from '@/entities/job/types';
import { useFetchJobs } from '@/features/fetch-jobs/FetchJobsProvider';
import { full } from '@/shared/lib/format';
import { IconButton, ProgressBar } from '@/shared/ui';

function progressText(job: FetchJobRecord) {
  if (job.total) return `${job.stage} ${full(job.done)}/${full(job.total)}`;
  if (job.done > 0) return `${job.stage} (${full(job.done)} video)`;
  return job.stage;
}

function JobRow({ job, onDismiss }: { job: FetchJobRecord; onDismiss: () => void }) {
  const running = job.status === 'running';
  const label = job.kind === 'register' ? `Thêm ${job.label}` : `Đồng bộ ${job.label}`;
  const target = job.status === 'success' && job.channel_id ? `/channels/${job.channel_id}` : null;
  return (
    <li className="flex items-start gap-3 px-3 py-2.5">
      {running ? (
        <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin text-blue" aria-hidden />
      ) : job.status === 'success' ? (
        <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-up" aria-hidden />
      ) : (
        <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-text" aria-hidden />
      )}
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold">
          {target ? (
            <Link to={target} className="hover:underline">
              {label}
            </Link>
          ) : (
            label
          )}
        </p>
        <p className="text-xs text-muted">{running ? progressText(job) : job.message || job.stage}</p>
        {running && job.total ? (
          <ProgressBar value={(job.done / job.total) * 100} label={label} className="mt-1.5" />
        ) : null}
      </div>
      {running ? null : (
        <IconButton label="Ẩn" onClick={onDismiss}>
          <X className="h-4 w-4" aria-hidden />
        </IconButton>
      )}
    </li>
  );
}

export function FetchDock() {
  const { jobs, dismiss, dismissFinished } = useFetchJobs();
  const [open, setOpen] = useState(true);
  if (jobs.length === 0) return null;
  const running = jobs.filter((job) => job.status === 'running').length;
  const hasFinished = running < jobs.length;

  return (
    <section
      aria-label="Tiến trình lấy dữ liệu"
      className="fixed bottom-4 right-4 z-50 w-[min(360px,calc(100vw-2rem))] animate-pop-in-up overflow-hidden rounded-card border border-border bg-card shadow-pop"
    >
      <div className="flex items-center gap-2 border-b border-border px-3 py-2">
        {running > 0 ? <Loader2 className="h-4 w-4 animate-spin text-blue" aria-hidden /> : null}
        <p className="flex-1 text-sm font-bold">
          {running > 0 ? `Đang lấy dữ liệu (${running})` : 'Lấy dữ liệu đã xong'}
        </p>
        {hasFinished ? (
          <button type="button" onClick={dismissFinished} className="text-xs text-muted hover:text-fg">
            Xóa đã xong
          </button>
        ) : null}
        <IconButton label={open ? 'Thu gọn' : 'Mở rộng'} onClick={() => setOpen((value) => !value)}>
          {open ? <ChevronDown className="h-4 w-4" aria-hidden /> : <ChevronUp className="h-4 w-4" aria-hidden />}
        </IconButton>
      </div>
      {open ? (
        <ul className="max-h-[50vh] divide-y divide-border overflow-y-auto">
          {jobs.map((job) => (
            <JobRow key={job.id} job={job} onDismiss={() => dismiss(job.id)} />
          ))}
        </ul>
      ) : null}
    </section>
  );
}
