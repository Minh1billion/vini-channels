import { AlertTriangle, CheckCircle2, Loader, XCircle, type LucideIcon } from 'lucide-react';
import { cn } from '@/shared/lib/cn';
import type { SyncStatus } from './types';

const config: Record<SyncStatus, { label: string; icon: LucideIcon; iconClass: string }> = {
  success: { label: 'Thành công', icon: CheckCircle2, iconClass: 'text-blue' },
  partial: { label: 'Một phần', icon: AlertTriangle, iconClass: 'text-fg' },
  failed: { label: 'Thất bại', icon: XCircle, iconClass: 'text-fg' },
  running: { label: 'Đang chạy', icon: Loader, iconClass: 'text-muted' },
};

export function SyncStatusBadge({ status }: { status: SyncStatus }) {
  const { label, icon: Icon, iconClass } = config[status];
  return (
    <span className="inline-flex h-6 items-center gap-1 rounded-full border border-border bg-card px-2 text-xs font-medium">
      <Icon className={cn('h-3.5 w-3.5', iconClass)} aria-hidden />
      {label}
    </span>
  );
}
