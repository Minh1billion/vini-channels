import { ArrowUpRight, PlugZap } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Skeleton } from '@/shared/ui';

interface Props {
  data?: { expiring: number; revoked: number };
}

export function ConnectionCard({ data }: Props) {
  if (!data) return <Skeleton className="min-h-[134px] rounded-card" />;
  const healthy = data.expiring === 0 && data.revoked === 0;
  return (
    <Link
      to="/channels"
      className="group relative flex min-h-[134px] flex-col justify-between rounded-card border border-border bg-card p-4 hover:bg-surface"
    >
      <span className="flex items-center gap-2 text-sm">
        <PlugZap className="h-4 w-4 text-up" aria-hidden />
        Kết nối
      </span>
      <ArrowUpRight className="absolute right-4 top-4 h-4 w-4 text-up" aria-hidden />
      {healthy ? (
        <div>
          <p className="text-lg font-medium leading-6">Mọi kết nối đều ổn</p>
          <p className="mt-0.5 text-[13px] text-muted">Không có token sắp hết hạn hay kênh mất quyền.</p>
        </div>
      ) : (
        <p className="text-lg font-medium leading-6">
          {data.expiring} token sắp hết hạn, {data.revoked} kênh đã mất quyền truy cập
        </p>
      )}
    </Link>
  );
}
