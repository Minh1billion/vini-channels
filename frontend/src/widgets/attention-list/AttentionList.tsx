import { AlertTriangle, ArrowRight, CheckCircle2, Clock, Plus, ShieldOff, type LucideIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ChannelAvatar } from '@/entities/channel/ChannelAvatar';
import type { AttentionItem } from '@/entities/dashboard/types';
import { EmptyState, Skeleton, Widget } from '@/shared/ui';

const icons: Record<AttentionItem['kind'], { icon: LucideIcon; className: string }> = {
  revoked: { icon: ShieldOff, className: 'text-fg' },
  failing: { icon: AlertTriangle, className: 'text-fg' },
  expiring: { icon: Clock, className: 'text-fg' },
};

export function AttentionList({ data }: { data?: AttentionItem[] }) {
  return (
    <Widget
      title="Việc cần xử lý"
      className="h-full"
      actions={
        <span className="flex items-center gap-1">
          <Link to="/channels" aria-label="Gửi liên kết cấp quyền" title="Gửi liên kết cấp quyền" className="inline-flex h-7 w-7 items-center justify-center rounded-full text-up transition-colors hover:bg-surface">
            <Plus className="h-4 w-4" aria-hidden />
          </Link>
          <Link to="/sync" aria-label="Xem tất cả" title="Xem tất cả" className="inline-flex h-7 w-7 items-center justify-center rounded-full text-up transition-colors hover:bg-surface">
            <ArrowRight className="h-4 w-4" aria-hidden />
          </Link>
        </span>
      }
    >
      {!data ? (
        <div className="flex flex-col gap-2 p-3">
          <Skeleton className="h-10" />
          <Skeleton className="h-10" />
          <Skeleton className="h-10" />
        </div>
      ) : data.length === 0 ? (
        <EmptyState icon={CheckCircle2} title="Mọi thứ đang ổn" description="Token sắp hết hạn, kênh mất quyền hoặc lỗi đồng bộ sẽ hiện ở đây." />
      ) : (
        <ul className="max-h-[152px] overflow-y-auto">
          {data.map((item) => {
            const { icon: Icon, className } = icons[item.kind];
            return (
              <li key={item.id} className="flex h-[50px] items-center gap-3 border-b border-border px-4 last:border-b-0">
                <Icon className={`h-4 w-4 shrink-0 ${className}`} aria-hidden />
                <ChannelAvatar name={item.handle} tone={item.tone} src={item.avatarUrl} size={24} />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm">
                    <span className="font-medium">{item.handle}</span> · {item.message}
                  </span>
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </Widget>
  );
}

