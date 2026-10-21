import { Archive, AtSign, Search } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ChannelAvatar } from '@/entities/channel/ChannelAvatar';
import { ChannelCard } from '@/entities/channel/ChannelCard';
import { StatusBadge } from '@/entities/channel/StatusBadge';
import { toneFor } from '@/entities/channel/tone';
import type { ChannelRecord } from '@/entities/channel/types';
import { useAuth } from '@/features/auth/AuthProvider';
import { RangePicker } from '@/features/period-picker/RangePicker';
import { AddChannelDialog } from '@/features/channel-forms/AddChannelDialog';
import { useOnJobFinished } from '@/features/fetch-jobs/FetchJobsProvider';
import { ChannelDialog } from '@/features/channel-forms/ChannelDialog';
import { analyticsApi, channelsApi, partnersApi } from '@/shared/api';
import { signedCount } from '@/entities/analytics/kpis';
import { compact, percent } from '@/shared/lib/format';
import { lastDays, periodKey, periodLabel, type Period } from '@/shared/lib/period';
import { errorMessage } from '@/shared/lib/errors';
import { useAsync } from '@/shared/lib/useAsync';
import { useDebounced } from '@/shared/lib/useDebounced';
import { useViewMode } from '@/shared/lib/useViewMode';
import {
  Button,
  CheckboxField,
  Chip,
  DataTable,
  EmptyState,
  FormError,
  SelectField,
  Skeleton,
  ViewToggle,
  Widget,
  useConfirm,
  type Column,
} from '@/shared/ui';
import { PageHeader } from '@/widgets/page-header/PageHeader';

export function ChannelsPage() {
  const { can } = useAuth();
  const canWrite = can('partners:write');
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState(params.get('q') ?? '');
  const [partnerId, setPartnerId] = useState(params.get('partner_id') ?? '');
  const [archived, setArchived] = useState(false);
  const [period, setPeriod] = useState<Period>(lastDays(30));
  const [editing, setEditing] = useState<ChannelRecord | 'new' | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [view, setView] = useViewMode('vc-view-channels');
  const debounced = useDebounced(query);
  const confirm = useConfirm();

  const partners = useAsync(() => partnersApi.list({ include_archived: true }), []);
  const overview = useAsync(() => analyticsApi.overview(period), [periodKey(period)]);
  const channels = useAsync(
    () => channelsApi.list({ q: debounced, partner_id: partnerId, include_archived: archived }),
    [debounced, partnerId, archived],
  );

  useEffect(() => {
    if (!canWrite) return;
    if (params.get('new')) {
      setEditing('new');
      setParams({}, { replace: true });
    }
  }, [params, canWrite, setParams]);

  const partnerNames = useMemo(
    () => new Map((partners.data ?? []).map((partner) => [partner.id, partner.name])),
    [partners.data],
  );

  const stats = useMemo(
    () => new Map((overview.data?.channels ?? []).map((item) => [item.channel_id, item])),
    [overview.data],
  );

  const periodText = periodLabel(period);

  const refresh = () => {
    channels.reload();
    overview.reload();
    partners.reload();
  };

  useOnJobFinished(refresh);

  const toggleArchive = async (channel: ChannelRecord) => {
    if (
      !channel.archived_at &&
      !(await confirm({
        title: 'Lưu trữ kênh này?',
        message: `Kênh @${channel.handle} sẽ được chuyển vào mục lưu trữ. Bạn có thể khôi phục lại sau.`,
        confirmLabel: 'Lưu trữ',
        icon: Archive,
      }))
    )
      return;
    setActionError(null);
    try {
      if (channel.archived_at) await channelsApi.restore(channel.id);
      else await channelsApi.archive(channel.id);
      refresh();
    } catch (err) {
      setActionError(errorMessage(err));
    }
  };

  const columns: Array<Column<ChannelRecord>> = [
    {
      key: 'channel',
      header: 'Kênh',
      cell: (row) => (
        <span className="flex items-center gap-3 py-1.5">
          <ChannelAvatar name={row.display_name || row.handle} tone={toneFor(row.id)} src={row.avatar_url} size={32} />
          <span className="min-w-0">
            <Link
              to={`/channels/${row.id}`}
              className={row.archived_at ? 'block truncate text-muted underline-offset-4 hover:underline hover:decoration-up' : 'block truncate font-medium underline-offset-4 hover:underline hover:decoration-up'}
            >
              {row.display_name || `@${row.handle}`}
            </Link>
            <span className="block truncate font-mono text-xs text-muted">@{row.handle}</span>
          </span>
        </span>
      ),
    },
    { key: 'partner', header: 'Đối tác', cell: (row) => partnerNames.get(row.partner_id) ?? '—' },
    {
      key: 'followers',
      header: 'Người theo dõi',
      align: 'right',
      cell: (row) => {
        const item = stats.get(row.id);
        return item?.followers == null ? '—' : compact(item.followers);
      },
    },
    {
      key: 'growth',
      header: 'Tăng trưởng',
      align: 'right',
      cell: (row) => {
        const item = stats.get(row.id);
        return item ? signedCount(item.follower_growth) : '—';
      },
    },
    {
      key: 'views',
      header: 'Lượt xem',
      align: 'right',
      cell: (row) => {
        const item = stats.get(row.id);
        return item ? compact(item.views) : '—';
      },
    },
    {
      key: 'erv',
      header: 'Tương tác',
      align: 'right',
      cell: (row) => percent(stats.get(row.id)?.erv),
    },
    {
      key: 'status',
      header: 'Trạng thái',
      cell: (row) =>
        row.archived_at ? <Chip>Đã lưu trữ</Chip> : <StatusBadge status={row.status} />,
    },
    {
      key: 'mode',
      header: 'Kết nối',
      cell: (row) => (row.connection_mode === 'authorized' ? 'Ủy quyền' : 'Công khai'),
    },
    {
      key: 'schedule',
      header: 'Lịch đồng bộ',
      cell: (row) => <span className="font-mono text-xs">{row.sync_cron ?? 'Mặc định'}</span>,
    },
  ];

  if (canWrite) {
    columns.push({
      key: 'actions',
      header: '',
      align: 'right',
      cell: (row) => (
        <span className="flex justify-end gap-1">
          {row.archived_at ? null : (
            <Button variant="secondary" size="sm" onClick={() => setEditing(row)}>
              Cập nhật
            </Button>
          )}
          <Button variant="ghost" size="sm" onClick={() => toggleArchive(row)}>
            {row.archived_at ? 'Khôi phục' : 'Lưu trữ'}
          </Button>
        </span>
      ),
    });
  }

  const rows = channels.data;

  return (
    <>
      <PageHeader
        icon={AtSign}
        title="Kênh"
        description="Danh sách kênh TikTok đang theo dõi cùng trạng thái và hiệu quả của từng kênh."
        actions={
          canWrite ? (
            <Button variant="primary" onClick={() => setEditing('new')}>
              <AtSign className="h-4 w-4" aria-hidden />
              Thêm kênh
            </Button>
          ) : null
        }
      />

      <div className="mb-2 flex flex-wrap items-end gap-4">
        <label className="relative w-full max-w-xs">
          <span className="sr-only">Tìm kênh</span>
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" aria-hidden />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Tìm theo handle hoặc tên..."
            className="h-10 w-full rounded-field border border-border bg-card pl-8 pr-3 text-sm placeholder:text-muted focus:border-fg focus:outline-none"
          />
        </label>
        <SelectField
          label="Lọc theo đối tác"
          hideLabel
          value={partnerId}
          onChange={(e) => setPartnerId(e.target.value)}
          className="w-52"
        >
          <option value="">Tất cả đối tác</option>
          {(partners.data ?? []).map((partner) => (
            <option key={partner.id} value={partner.id}>
              {partner.name}
            </option>
          ))}
        </SelectField>
        <CheckboxField
          label="Hiện đã lưu trữ"
          checked={archived}
          onChange={(e) => setArchived(e.target.checked)}
          className="h-10"
        />
        <div className="ml-auto flex items-center gap-2">
          <RangePicker value={period} onChange={setPeriod} align="end" />
          <ViewToggle value={view} onChange={setView} />
        </div>
      </div>
      <div className="mb-2" />

      <FormError message={actionError} />

      {view === 'cards' && rows && rows.length > 0 && !channels.error ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
          {rows.map((row) => (
            <ChannelCard
              key={row.id}
              channel={row}
              partnerName={partnerNames.get(row.partner_id)}
              stat={stats.get(row.id)}
              periodText={periodText}
              canWrite={canWrite}
              onEdit={setEditing}
              onToggleArchive={toggleArchive}
            />
          ))}
        </div>
      ) : (
      <Widget>
        {!rows && channels.loading ? (
          view === 'cards' ? (
            <div className="grid gap-4 p-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
              {Array.from({ length: 6 }, (_, i) => (
                <Skeleton key={i} className="h-72" />
              ))}
            </div>
          ) : (
            <div className="flex flex-col gap-2 p-4">
              {Array.from({ length: 5 }, (_, i) => (
                <Skeleton key={i} className="h-10" />
              ))}
            </div>
          )
        ) : channels.error ? (
          <EmptyState
            icon={AtSign}
            title="Không tải được danh sách kênh"
            description={errorMessage(channels.error)}
            action={<Button variant="secondary" onClick={channels.reload}>Thử lại</Button>}
          />
        ) : rows && rows.length === 0 ? (
          <EmptyState
            icon={AtSign}
            title="Chưa có kênh"
            description={debounced || partnerId ? 'Không có kênh khớp bộ lọc.' : 'Thêm kênh đầu tiên.'}
            action={
              canWrite && !debounced && !partnerId ? (
                <Button variant="secondary" onClick={() => setEditing('new')}>
                  <AtSign className="h-4 w-4" aria-hidden />
                  Thêm kênh
                </Button>
              ) : undefined
            }
          />
        ) : (
          <DataTable columns={columns} rows={rows ?? []} rowKey={(row) => row.id} caption={`Danh sách kênh, thông số ${periodText}`} />
        )}
      </Widget>
      )}

      {editing === 'new' ? (
        <AddChannelDialog
          partners={partners.data ?? []}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            refresh();
          }}
        />
      ) : editing ? (
        <ChannelDialog
          channel={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            refresh();
          }}
        />
      ) : null}
    </>
  );
}
