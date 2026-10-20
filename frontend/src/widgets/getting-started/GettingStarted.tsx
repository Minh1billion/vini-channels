import { ArrowRight, Check } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { DashboardData } from '@/entities/dashboard/types';
import { useAuth } from '@/features/auth/AuthProvider';
import { providersApi } from '@/shared/api';
import { cn } from '@/shared/lib/cn';
import { useAsync } from '@/shared/lib/useAsync';
import { ProgressBar, Widget } from '@/shared/ui';

interface Step {
  id: string;
  title: string;
  description: string;
  to: string;
  done: boolean;
}

export function GettingStarted({ data }: { data?: DashboardData }) {
  const { can } = useAuth();
  const canSeeProviders = can('providers:write');
  const providers = useAsync(
    () => (canSeeProviders ? providersApi.list() : Promise.resolve(null)),
    [canSeeProviders],
  );

  if (!data || (canSeeProviders && providers.loading && !providers.data)) return null;

  const steps: Step[] = [];
  if (canSeeProviders) {
    steps.push({
      id: 'provider',
      title: 'Bật nguồn dữ liệu',
      description: 'Nhập khóa API cho ít nhất một nguồn để lấy số liệu kênh.',
      to: '/settings/providers',
      done: (providers.data ?? []).some((provider) => provider.enabled),
    });
  }
  if (can('partners:write')) {
    steps.push(
      {
        id: 'partner',
        title: 'Thêm đối tác đầu tiên',
        description: 'Đối tác là công ty hoặc thương hiệu sở hữu các kênh.',
        to: '/partners?new=1',
        done: data.counts.partners > 0,
      },
      {
        id: 'channel',
        title: 'Thêm kênh TikTok',
        description: 'Nhập handle của kênh cần theo dõi và chọn nguồn dữ liệu.',
        to: '/channels?new=1',
        done: data.counts.channels > 0,
      },
    );
  }
  if (can('sync:write')) {
    steps.push({
      id: 'sync',
      title: 'Đồng bộ lần đầu',
      description: 'Chạy đồng bộ để có người theo dõi, lượt xem và video.',
      to: '/sync',
      done: (data.sync?.runs.length ?? 0) > 0,
    });
  }

  const completed = steps.filter((step) => step.done).length;
  if (steps.length === 0 || completed === steps.length) return null;
  const next = steps.find((step) => !step.done);

  return (
    <Widget
      title="Bắt đầu với ViniChannels"
      actions={<span className="pr-2 text-[13px] text-muted">{completed}/{steps.length} bước</span>}
      bodyClassName="flex flex-col"
    >
      <div className="px-4 pt-4">
        <ProgressBar value={(completed / steps.length) * 100} label="Tiến độ thiết lập" />
      </div>
      <ol className="mt-2 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4">
        {steps.map((step, index) => {
          const current = step.id === next?.id;
          return (
            <li key={step.id} className="border-b border-border last:border-b-0 md:[&:nth-last-child(-n+2):nth-child(odd)]:border-b-0 xl:border-b-0 xl:border-r xl:last:border-r-0">
              <Link
                to={step.to}
                aria-current={current ? 'step' : undefined}
                className={cn('group flex h-full items-start gap-3 p-4 hover:bg-surface', current && 'bg-surface')}
              >
                <span
                  aria-hidden
                  className={cn(
                    'mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-[13px] font-medium',
                    step.done ? 'border-transparent bg-blue text-on-blue' : 'border-border',
                    current && !step.done && 'border-transparent bg-blue text-on-blue',
                  )}
                >
                  {step.done ? <Check className="h-3.5 w-3.5" /> : index + 1}
                </span>
                <span className="min-w-0 flex-1">
                  <span className={cn('block text-sm font-bold', step.done && 'text-muted line-through')}>{step.title}</span>
                  <span className="mt-0.5 block text-[13px] text-muted">{step.description}</span>
                </span>
                {step.done ? (
                  <span className="sr-only">Đã xong</span>
                ) : current ? (
                  <span aria-hidden className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue text-on-blue transition-colors group-hover:brightness-95">
                    <ArrowRight className="h-3.5 w-3.5" />
                  </span>
                ) : (
                  <ArrowRight className="mt-1 h-4 w-4 shrink-0 text-up" aria-hidden />
                )}
              </Link>
            </li>
          );
        })}
      </ol>
    </Widget>
  );
}
