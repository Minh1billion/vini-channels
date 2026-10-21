import { CheckCircle2, Database, Hourglass } from 'lucide-react';
import { cn } from '@/shared/lib/cn';

export function NeedsBadge({ kind }: { kind: 'single' | 'multi' }) {
  const single = kind === 'single';
  return (
    <span
      title={
        single
          ? 'Tính được ngay từ lần đồng bộ đầu tiên'
          : 'Cần so sánh giữa ít nhất hai lần đồng bộ ở các ngày khác nhau'
      }
      className={cn(
        'inline-flex h-5 items-center whitespace-nowrap rounded-full border px-2 text-[11px] font-medium',
        single ? 'border-blue text-blue' : 'border-border text-muted',
      )}
    >
      {single ? '1 lần đồng bộ' : '≥ 2 lần đồng bộ'}
    </span>
  );
}

interface Props {
  syncDays?: number;
  videoCount?: number;
  hasCurve?: boolean;
}

export function DataReadiness({ syncDays, videoCount, hasCurve }: Props) {
  if (syncDays === undefined || videoCount === undefined) return null;

  const empty = syncDays === 0 && videoCount === 0;
  const ready = syncDays >= 2;
  const Icon = empty ? Database : ready ? CheckCircle2 : Hourglass;

  const message = empty
    ? 'Chưa có dữ liệu trong kỳ này. Đồng bộ kênh một lần để xem tab Hiện trạng.'
    : ready
      ? `Đã có dữ liệu của ${syncDays} ngày trong kỳ nên các biểu đồ xu hướng đã vẽ được.${
          hasCurve === false ? ' Đường tăng trưởng từng video cần thêm lần đồng bộ ở các ngày khác nhau sau khi đăng.' : ''
        }`
      : `Mới có dữ liệu của ${syncDays} ngày. Tab Hiện trạng dùng được ngay; tab Xu hướng cần thêm ít nhất 1 ngày đồng bộ nữa.`;

  return (
    <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-2 rounded-card border border-border bg-card px-4 py-3 text-sm">
      <p className="flex min-w-0 items-start gap-2">
        <Icon className="mt-0.5 h-4 w-4 shrink-0 text-blue" aria-hidden />
        <span>{message}</span>
      </p>
      <p className="flex items-center gap-2 text-[13px] text-muted">
        <NeedsBadge kind="single" />
        <NeedsBadge kind="multi" />
      </p>
    </div>
  );
}
