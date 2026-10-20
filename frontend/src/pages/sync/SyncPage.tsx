import { RefreshCw, ShieldOff } from 'lucide-react';
import { useState } from 'react';
import { ChannelAvatar } from '@/entities/channel/ChannelAvatar';
import { toneFor } from '@/entities/channel/tone';
import { sourceLabel } from '@/entities/provider/labels';
import { SourceTag } from '@/entities/provider/ProviderLogo';
import { describeCron } from '@/entities/sync/cron';
import { SyncStatusBadge } from '@/entities/sync/SyncStatusBadge';
import type { SyncRunRecord, SyncScheduleRecord, SyncStatus } from '@/entities/sync/types';
import { useAuth } from '@/features/auth/AuthProvider';
import { syncApi } from '@/shared/api';
import { dateTime, duration, full, relativeTime, untilTime } from '@/shared/lib/format';
import { errorMessage } from '@/shared/lib/errors';
import { useAsync } from '@/shared/lib/useAsync';
import { Button, Chip, DataTable, EmptyState, FormError, SelectField, Skeleton, Tabs, Widget, type Column } from '@/shared/ui';
import { PageHeader } from '@/widgets/page-header/PageHeader';

type TabId = 'runs' | 'schedules';

const tabs: Array<{ id: TabId; label: string }> = [
  { id: 'runs', label: 'Nhật ký' },
  { id: 'schedules', label: 'Lịch theo kênh' },
];

const STATUS_OPTIONS: Array<{ value: SyncStatus | ''; label: string }> = [
  { value: '', label: 'Mọi trạng thái' },
  { value: 'success', label: 'Thành công' },
  { value: 'partial', label: 'Một phần' },
  { value: 'failed', label: 'Thất bại' },
  { value: 'running', label: 'Đang chạy' },
];

function ChannelCell({ id, handle }: { id: string; handle: string }) {
  return (
    <span className="flex items-center gap-2.5">
      <ChannelAvatar name={handle} tone={toneFor(id)} size={24} />
      <span className="font-medium">@{handle}</span>
    </span>
  );
}

const runColumns: Array<Column<SyncRunRecord>> = [
  { key: 'channel', header: 'Kênh', cell: (r) => <ChannelCell id={r.channel_id} handle={r.handle} /> },
  { key: 'status', header: 'Trạng thái', cell: (r) => <SyncStatusBadge status={r.status} /> },
  { key: 'source', header: 'Nguồn', cell: (r) => <SourceTag source={r.source} /> },
  { key: 'items', header: 'Số mục', align: 'right', cell: (r) => full(r.items_fetched) },
  {
    key: 'duration',
    header: 'Thời lượng',
    align: 'right',
    cell: (r) => duration(r.duration_sec === null ? null : Math.round(r.duration_sec)),
  },
  { key: 'trigger', header: 'Kích hoạt', cell: (r) => (r.trigger === 'manual' ? 'Thủ công' : 'Theo lịch') },
  {
    key: 'started',
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
  {
    key: 'error',
    header: 'Lỗi',
    className: 'max-w-[280px]',
    cell: (r) =>
      r.error_message ? (
        <span className="block truncate text-down" title={`${r.error_code ?? ''} ${r.error_message}`.trim()}>
          {r.error_message}
        </span>
      ) : (
        <span className="text-muted">—</span>
      ),
  },
];

export function SyncPage() {
  const { can } = useAuth();
  const canRead = can('sync:read');
  const canSync = can('sync:write');
  const [tab, setTab] = useState<TabId>('runs');
  const [status, setStatus] = useState<SyncStatus | ''>('');
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const runs = useAsync(() => (canRead ? syncApi.runs({ limit: 100, status: status || undefined }) : Promise.resolve([])), [
    status,
    canRead,
  ]);
  const schedules = useAsync(() => (canRead ? syncApi.schedules() : Promise.resolve([])), [canRead]);

  const reloadAll = () => {
    runs.reload();
    schedules.reload();
  };

  const syncNow = async (row: SyncScheduleRecord) => {
    setBusy(row.channel_id);
    setNotice(null);
    setActionError(null);
    try {
      const run = await syncApi.syncChannel(row.channel_id);
      const label = `@${row.handle}: ${sourceLabel(run.source)}, ${full(run.items_fetched)} mục`;
      if (run.status === 'failed') setActionError(`${label}. ${run.error_message ?? 'Đồng bộ thất bại'}`);
      else setNotice(`Đã đồng bộ ${label}`);
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setBusy(null);
      reloadAll();
    }
  };

  if (!canRead) {
    return (
      <>
        <PageHeader
        icon={RefreshCw}
        title="Đồng bộ"
        description="Theo dõi lịch và kết quả các lần đồng bộ dữ liệu từ nguồn."
      />
        <Widget>
          <EmptyState icon={ShieldOff} title="Bạn không có quyền" description="Vai trò của bạn không xem được nhật ký đồng bộ." />
        </Widget>
      </>
    );
  }

  const scheduleColumns: Array<Column<SyncScheduleRecord>> = [
    { key: 'channel', header: 'Kênh', cell: (r) => <ChannelCell id={r.channel_id} handle={r.handle} /> },
    {
      key: 'cron',
      header: 'Lịch',
      cell: (r) => (
        <span className="flex flex-col py-1">
          <span>
            {describeCron(r.cron) ?? 'Tùy chỉnh'}
            {r.is_default_cron ? <span className="text-muted"> (mặc định)</span> : null}
          </span>
          <span className="font-mono text-xs text-muted">{r.cron}</span>
        </span>
      ),
    },
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
      header: 'Kết nối',
      cell: (r) => <Chip>{r.connection_mode === 'authorized' ? 'Ủy quyền' : 'Công khai'}</Chip>,
    },
  ];

  if (canSync) {
    scheduleColumns.push({
      key: 'actions',
      header: '',
      align: 'right',
      cell: (r) => (
        <Button variant="secondary" size="sm" disabled={busy !== null || !r.is_active} onClick={() => syncNow(r)}>
          <RefreshCw className={busy === r.channel_id ? 'h-3.5 w-3.5 animate-spin' : 'h-3.5 w-3.5'} aria-hidden />
          {busy === r.channel_id ? 'Đang đồng bộ...' : 'Đồng bộ ngay'}
        </Button>
      ),
    });
  }

  const skeleton = (
    <div className="flex flex-col gap-2 p-4">
      {Array.from({ length: 5 }, (_, i) => (
        <Skeleton key={i} className="h-10" />
      ))}
    </div>
  );

  const failed = (error: Error, reload: () => void) => (
    <EmptyState
      icon={RefreshCw}
      title="Không tải được dữ liệu"
      description={errorMessage(error)}
      action={<Button variant="secondary" onClick={reload}>Thử lại</Button>}
    />
  );

  return (
    <>
      <PageHeader
        icon={RefreshCw}
        title="Đồng bộ"
        description="Theo dõi lịch và kết quả các lần đồng bộ dữ liệu từ nguồn."
        actions={
          <Button variant="primary" onClick={reloadAll}>
            <RefreshCw className="h-4 w-4" aria-hidden />
            Làm mới
          </Button>
        }
      />

      <Tabs tabs={tabs} value={tab} onChange={setTab} label="Đồng bộ" />

      <div className="mt-4 flex flex-col gap-3">
        {notice ? (
          <p role="status" className="text-sm text-blue">
            {notice}
          </p>
        ) : null}
        <FormError message={actionError} />

        {tab === 'runs' ? (
          <>
            <SelectField
              label="Lọc theo trạng thái"
              hideLabel
              value={status}
              onChange={(e) => setStatus(e.target.value as SyncStatus | '')}
              className="w-52"
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </SelectField>
            <Widget>
              {!runs.data && runs.loading ? (
                skeleton
              ) : runs.error ? (
                failed(runs.error, runs.reload)
              ) : runs.data && runs.data.length === 0 ? (
                <EmptyState
                  icon={RefreshCw}
                  title="Chưa có lần đồng bộ nào"
                  description={status ? 'Không có lần chạy khớp bộ lọc.' : 'Đồng bộ thủ công một kênh ở tab Lịch theo kênh.'}
                />
              ) : (
                <DataTable
                  caption="Nhật ký đồng bộ"
                  columns={runColumns}
                  rows={runs.data ?? []}
                  rowKey={(r) => r.id}
                  id="panel-runs"
                  labelledBy="tab-runs"
                />
              )}
            </Widget>
          </>
        ) : (
          <Widget>
            {!schedules.data && schedules.loading ? (
              skeleton
            ) : schedules.error ? (
              failed(schedules.error, schedules.reload)
            ) : schedules.data && schedules.data.length === 0 ? (
              <EmptyState icon={RefreshCw} title="Chưa có kênh" description="Thêm kênh ở màn hình Kênh để bắt đầu đồng bộ." />
            ) : (
              <DataTable
                caption="Lịch đồng bộ của từng kênh"
                columns={scheduleColumns}
                rows={schedules.data ?? []}
                rowKey={(r) => r.channel_id}
                id="panel-schedules"
                labelledBy="tab-schedules"
              />
            )}
          </Widget>
        )}
      </div>
    </>
  );
}
