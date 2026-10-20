import { AlertTriangle, CheckCircle2, Clock, EyeOff, SearchX, ShieldOff, type LucideIcon } from 'lucide-react';
import { cn } from '@/shared/lib/cn';
import type { ChannelStatus } from './types';

const config: Record<ChannelStatus, { label: string; icon: LucideIcon; iconClass: string }> = {
  healthy: { label: 'Hoạt động', icon: CheckCircle2, iconClass: 'text-blue' },
  token_expiring: { label: 'Sắp hết hạn', icon: Clock, iconClass: 'text-fg' },
  token_revoked: { label: 'Mất quyền', icon: ShieldOff, iconClass: 'text-fg' },
  not_found: { label: 'Không tìm thấy', icon: SearchX, iconClass: 'text-fg' },
  private: { label: 'Riêng tư', icon: EyeOff, iconClass: 'text-muted' },
  provider_error: { label: 'Lỗi nguồn', icon: AlertTriangle, iconClass: 'text-fg' },
};

export function StatusBadge({ status, className }: { status: ChannelStatus; className?: string }) {
  const { label, icon: Icon, iconClass } = config[status];
  return (
    <span
      className={cn(
        'inline-flex h-6 items-center gap-1 rounded-full border border-border bg-card px-2 text-xs font-medium',
        className,
      )}
    >
      <Icon className={cn('h-3.5 w-3.5', iconClass)} aria-hidden />
      {label}
    </span>
  );
}
