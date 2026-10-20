import { ArrowRight, LayoutDashboard } from 'lucide-react';
import { Link } from 'react-router-dom';
import { AddMenu } from '@/features/add-menu/AddMenu';
import { useAuth } from '@/features/auth/AuthProvider';
import { overviewKpis } from '@/entities/analytics/kpis';
import { dashboardApi } from '@/shared/api';
import { cn } from '@/shared/lib/cn';
import { errorMessage } from '@/shared/lib/errors';
import { useAsync } from '@/shared/lib/useAsync';
import { Button } from '@/shared/ui';
import { GettingStarted } from '@/widgets/getting-started/GettingStarted';
import { KpiRow } from '@/widgets/kpi-row/KpiRow';
import { AttentionList } from '@/widgets/attention-list/AttentionList';
import { ConnectionCard } from '@/widgets/overview-cards/ConnectionCard';
import { QuickSearchCard } from '@/widgets/overview-cards/QuickSearchCard';
import { SyncHealthCard } from '@/widgets/overview-cards/SyncHealthCard';
import { PageHeader } from '@/widgets/page-header/PageHeader';
import { RecentChannels } from '@/widgets/recent-channels/RecentChannels';
import { SyncRunsTable } from '@/widgets/sync-runs-table/SyncRunsTable';

export function DashboardPage() {
  const { can } = useAuth();
  const includeSync = can('sync:read');
  const { data, error, reload } = useAsync(() => dashboardApi.load({ includeSync }), [includeSync]);

  return (
    <>
      <PageHeader
        icon={LayoutDashboard}
        title="Dashboard"
        description="Tổng quan hiệu quả các kênh đối tác trong 30 ngày gần nhất."
        actions={<AddMenu />}
      />

      {error ? (
        <div role="alert" className="mb-4 flex items-center justify-between gap-3 rounded-card border border-border bg-card p-4">
          <span className="text-down">{errorMessage(error, 'Không tải được dữ liệu')}</span>
          <Button variant="secondary" onClick={reload}>Thử lại</Button>
        </div>
      ) : null}

      <div className="flex flex-col gap-6">
        <GettingStarted data={data} />

        <KpiRow items={data ? overviewKpis(data.overview) : undefined} />

        <div
          className={cn(
            'grid grid-cols-1 gap-4 md:grid-cols-2',
            includeSync ? 'lg:grid-cols-[5fr_3fr_2fr]' : 'lg:grid-cols-[5fr_2fr]',
          )}
        >
          <div className="md:col-span-2 lg:col-span-1">
            <QuickSearchCard />
          </div>
          {includeSync ? <SyncHealthCard data={data?.sync?.health} /> : null}
          <ConnectionCard data={data?.connection} />
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <RecentChannels data={data?.recent} />
          <AttentionList data={data?.attention} />
        </div>

        {includeSync ? (
          <section>
            <div className="mb-3 flex items-center justify-between gap-2">
              <h2 className="text-base font-bold">Lần đồng bộ</h2>
              <Link to="/sync" className="inline-flex items-center gap-1 text-sm font-medium text-blue underline-offset-4 hover:underline hover:decoration-blue">
                Xem tất cả
                <ArrowRight className="h-3.5 w-3.5" aria-hidden />
              </Link>
            </div>
            <SyncRunsTable runs={data?.sync?.runs} schedules={data?.sync?.schedules} />
          </section>
        ) : null}
      </div>
    </>
  );
}
