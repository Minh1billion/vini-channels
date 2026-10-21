import { Timer } from 'lucide-react';
import { useLoadState } from '@/shared/lib/loadTimer';
import { cn } from '@/shared/lib/cn';

function formatDuration(ms: number) {
  return ms >= 1000 ? `${(ms / 1000).toFixed(2)} s` : `${ms} ms`;
}

export function LoadTimeBadge({ className }: { className?: string }) {
  const { status, ms } = useLoadState();
  if (status === 'idle') return null;
  const loading = status === 'loading';
  return (
    <div
      role="status"
      aria-live="polite"
      title="Thời gian từ lúc chuyển trang đến khi dữ liệu của trang tải xong"
      className={cn(
        'flex animate-fade-in items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted shadow-pop transition-colors',
        !loading && ms >= 1500 && 'text-red-text',
        className,
      )}
    >
      <Timer className={cn('h-3.5 w-3.5', loading && 'animate-pulse')} aria-hidden />
      {loading ? 'Đang tải nội dung…' : `Nội dung tải trong ${formatDuration(ms)}`}
    </div>
  );
}
