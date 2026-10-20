import { monthLabel } from '@/shared/lib/format';
import { Skeleton } from '@/shared/ui';
import type { SyncHealth } from '@/entities/sync/types';

const COLUMNS = 10;
const STEP = 14;

export function SyncHealthCard({ data }: { data?: SyncHealth }) {
  if (!data) return <Skeleton className="min-h-[134px] rounded-card" />;
  const failed = data.total - data.ok;
  const rows = Math.ceil(data.runs.length / COLUMNS);
  return (
    <section
      aria-label="Sức khỏe đồng bộ"
      className="relative min-h-[134px] overflow-hidden rounded-card border border-border bg-card p-4"
    >
      <p className="text-sm">Đồng bộ</p>
      <p className="text-sm text-muted">{monthLabel(data.month)}</p>
      {data.total === 0 ? (
        <p className="absolute bottom-4 left-4 text-sm text-muted">Chưa có lần đồng bộ nào trong tháng</p>
      ) : (
        <>
          <p className="absolute bottom-4 left-4 text-page font-bold">
            {data.ok}/{data.total}
            <span className="sr-only"> lần chạy thành công</span>
          </p>
          <svg
            role="img"
            aria-label={`${data.ok} trên ${data.total} lần chạy thành công, ${failed} lần thất bại`}
            viewBox={`0 0 ${COLUMNS * STEP} ${rows * STEP}`}
            className="absolute right-4 top-4 h-[calc(100%-2rem)] w-[48%] max-w-[190px]"
            preserveAspectRatio="xMaxYMid meet"
          >
            {data.runs.map((run, i) => {
              const cx = (i % COLUMNS) * STEP + STEP / 2;
              const cy = Math.floor(i / COLUMNS) * STEP + STEP / 2;
              return run === 'ok' ? (
                <circle key={i} cx={cx} cy={cy} r={2.4} fill="var(--up)" fillOpacity={0.55} />
              ) : (
                <circle key={i} cx={cx} cy={cy} r={4.6} fill="var(--fg)" />
              );
            })}
          </svg>
        </>
      )}
    </section>
  );
}
