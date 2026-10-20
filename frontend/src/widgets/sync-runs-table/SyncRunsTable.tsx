import { RefreshCw } from 'lucide-react';
import { useState } from 'react';
import { ChannelAvatar } from '@/entities/channel/ChannelAvatar';
import { toneFor } from '@/entities/channel/tone';
import { SourceTag } from '@/entities/provider/ProviderLogo';
import { describeCron } from '@/entities/sync/cron';
import { SyncStatusBadge } from '@/entities/sync/SyncStatusBadge';
import type { SyncRunRecord, SyncScheduleRecord } from '@/entities/sync/types';
import { dateTime, duration, full, relativeTime, untilTime } from '@/shared/lib/format';
import { Chip, DataTable, EmptyState, Skeleton, Tabs, type Column } from '@/shared/ui';

type TabId = 'recent' | 'scheduled';

const tabs: Array<{ id: TabId; label: string }> = [
  { id: 'recent', label: 'Gần đây' },
  { id: 'scheduled', label: 'Theo lịch' },
];

function ChannelCell({ id, handle }: { id: string; handle: string }) {
  return (
    <span className="flex items-center gap-2.5">
      <ChannelAvatar name={handle} tone={toneFor(id)} size={24} />
      <span className="font-medium">@{handle}</span>
    </span>
  );
}

const recentColumns: Array<Column<SyncRunRecord>> = [
  { key: 'channel', header: 'Kênh', cell: (r) => <ChannelCell id={r.channel_id} handle={r.handle} /> },
  { key: 'source', header: 'Nguồn', cell: (r) => <SourceTag source={r.source} /> },
  { key: 'status', header: 'Trạng thái', cell: (r) => <SyncStatusBadge status={r.status} /> },
  { key: 'items', header: 'Bản ghi', align: 'right', cell: (r) => full(r.items_fetched) },
  {
    key: 'duration',
    header: 'Thời lượng',
    align: 'right',
    cell: (r) => duration(r.duration_sec === null ? null : Math.round(r.duration_sec)),
  },
  { key: 'trigger', header: 'Kích hoạt', cell: (r) => (r.trigger === 'manual' ? 'Thủ công' : 'Theo lịch') },
  {
    key: 'startedAt',
    header: 'Bắt đầu',
    cell: (r) => {
      const date = new Date(r.started_at);
      return (
        <time dateTime={r.started_at} title={dateTime(date)}>
          {relativeTime(date)}
        </time>
      );
    },
  },
];

const scheduleColumns: Array<Column<SyncScheduleRecord>> = [
  { key: 'channel', header: 'Kênh', cell: (r) => <ChannelCell id={r.channel_id} handle={r.handle} /> },
  { key: 'cadence', header: 'Lịch', cell: (r) => describeCron(r.cron) ?? r.cron },
  { key: 'timezone', header: 'Múi giờ', cell: (r) => r.timezone },
  {
    key: 'next',
    header: 'Lần chạy kế tiếp',
    cell: (r) => {
      if (!r.next_run_at) return <span className="text-muted">Đang tạm dừng</span>;
      const date = new Date(r.next_run_at);
      return (
        <time dateTime={r.next_run_at} title={dateTime(date)}>
          {untilTime(date)}
        </time>
      );
    },
  },
  {
    key: 'mode',
    header: 'Chế độ',
    cell: (r) => <Chip>{r.connection_mode === 'authorized' ? 'Cấp quyền' : 'Công khai'}</Chip>,
  },
];

const SCHEDULE_ROWS = 5;

interface Props {
  runs?: SyncRunRecord[];
  schedules?: SyncScheduleRecord[];
}

export function SyncRunsTable({ runs, schedules }: Props) {
  const [tab, setTab] = useState<TabId>('recent');

  return (
    <div>
      <Tabs tabs={tabs} value={tab} onChange={setTab} label="Lần đồng bộ" />
      <div className="mt-3 overflow-hidden rounded-card border border-border bg-card">
        {tab === 'recent' ? (
          !runs ? (
            <Skeleton className="h-[200px]" />
          ) : runs.length === 0 ? (
            <EmptyState icon={RefreshCw} title="Chưa có lần đồng bộ nào" description="Lịch sử các lần chạy sẽ hiện ở đây sau khi bạn đồng bộ kênh đầu tiên." />
          ) : (
            <DataTable
              caption="Các lần đồng bộ gần đây"
              columns={recentColumns}
              rows={runs}
              rowKey={(r) => r.id}
              id="panel-recent"
              labelledBy="tab-recent"
            />
          )
        ) : !schedules ? (
          <Skeleton className="h-[200px]" />
        ) : schedules.length === 0 ? (
          <EmptyState icon={RefreshCw} title="Chưa có kênh nào" description="Mỗi kênh được thêm sẽ có lịch đồng bộ riêng, hiện ở đây." />
        ) : (
          <DataTable
            caption="Lịch đồng bộ của từng kênh"
            columns={scheduleColumns}
            rows={schedules.slice(0, SCHEDULE_ROWS)}
            rowKey={(r) => r.channel_id}
            id="panel-scheduled"
            labelledBy="tab-scheduled"
          />
        )}
      </div>
    </div>
  );
}
