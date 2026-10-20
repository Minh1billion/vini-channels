import { Archive, AtSign, Handshake, Search } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ChannelAvatar } from '@/entities/channel/ChannelAvatar';
import { toneFor } from '@/entities/channel/tone';
import { PartnerCard, type PartnerStats } from '@/entities/partner/PartnerCard';
import type { Partner } from '@/entities/partner/types';
import type { ChannelRecord } from '@/entities/channel/types';
import { useAuth } from '@/features/auth/AuthProvider';
import { RangePicker } from '@/features/period-picker/RangePicker';
import { PartnerDialog } from '@/features/partner-form/PartnerDialog';
import { analyticsApi, channelsApi, partnersApi } from '@/shared/api';
import { lastDays, periodKey, periodLabel, type Period } from '@/shared/lib/period';
import { errorMessage } from '@/shared/lib/errors';
import { useAsync } from '@/shared/lib/useAsync';
import { useDebounced } from '@/shared/lib/useDebounced';
import { useViewMode } from '@/shared/lib/useViewMode';
import { Button, CheckboxField, Chip, DataTable, EmptyState, FormError, Skeleton, ViewToggle, Widget, useConfirm, type Column } from '@/shared/ui';
import { PageHeader } from '@/widgets/page-header/PageHeader';

export function PartnersPage() {
  const { can } = useAuth();
  const canWrite = can('partners:write');
  const [params, setParams] = useSearchParams();
  const [query, setQuery] = useState(params.get('q') ?? '');
  const [archived, setArchived] = useState(false);
  const [period, setPeriod] = useState<Period>(lastDays(30));
  const [editing, setEditing] = useState<Partner | 'new' | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [view, setView] = useViewMode('vc-view-partners');
  const debounced = useDebounced(query);
  const confirm = useConfirm();

  const { data, loading, error, reload } = useAsync(
    () => partnersApi.list({ q: debounced, include_archived: archived }),
    [debounced, archived],
  );

  const allChannels = useAsync(() => channelsApi.list({}), []);
  const overview = useAsync(() => analyticsApi.overview(period), [periodKey(period)]);

  const channelsByPartner = useMemo(() => {
    const map = new Map<string, ChannelRecord[]>();
    for (const channel of allChannels.data ?? []) {
      const list = map.get(channel.partner_id) ?? [];
      list.push(channel);
      map.set(channel.partner_id, list);
    }
    return map;
  }, [allChannels.data]);

  const statsByPartner = useMemo(() => {
    const byChannel = new Map((overview.data?.channels ?? []).map((item) => [item.channel_id, item]));
    const map = new Map<string, PartnerStats>();
    for (const [partnerId, list] of channelsByPartner) {
      const stats: PartnerStats = { followers: 0, growth: 0, views: 0, videos: 0, hasData: false };
      for (const channel of list) {
        const item = byChannel.get(channel.id);
        if (!item) continue;
        stats.hasData = true;
        stats.followers += item.followers ?? 0;
        stats.growth += item.follower_growth;
        stats.views += item.views;
        stats.videos += item.video_count;
      }
      map.set(partnerId, stats);
    }
    return map;
  }, [channelsByPartner, overview.data]);

  useEffect(() => {
    if (params.get('new') && canWrite) {
      setEditing('new');
      setParams({}, { replace: true });
    }
  }, [params, canWrite, setParams]);

  const toggleArchive = async (partner: Partner) => {
    if (
      !partner.archived_at &&
      !(await confirm({
        title: 'Lưu trữ đối tác này?',
        message: `Đối tác "${partner.name}" sẽ được chuyển vào mục lưu trữ. Bạn có thể khôi phục lại sau.`,
        confirmLabel: 'Lưu trữ',
        icon: Archive,
      }))
    )
      return;
    setActionError(null);
    try {
      if (partner.archived_at) await partnersApi.restore(partner.id);
      else await partnersApi.archive(partner.id);
      reload();
    } catch (err) {
      setActionError(errorMessage(err));
    }
  };

  const columns: Array<Column<Partner>> = [
    {
      key: 'name',
      header: 'Đối tác',
      cell: (row) => (
        <span className="flex items-center gap-3">
          <ChannelAvatar name={row.name} tone={toneFor(row.id)} size={32} className={row.archived_at ? 'opacity-50' : undefined} />
          <span className={row.archived_at ? 'text-muted' : 'font-medium'}>{row.name}</span>
          {row.archived_at ? <Chip>Đã lưu trữ</Chip> : null}
        </span>
      ),
    },
    { key: 'industry', header: 'Ngành', cell: (row) => row.industry ?? <span className="text-muted">—</span> },
    {
      key: 'tags',
      header: 'Nhãn',
      cell: (row) =>
        row.tags.length === 0 ? (
          <span className="text-muted">—</span>
        ) : (
          <span className="flex flex-wrap gap-1">
            {row.tags.map((tag) => (
              <Chip key={tag} className="h-6 gap-1.5 px-2.5 text-xs">
                <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-blue" />
                {tag}
              </Chip>
            ))}
          </span>
        ),
    },
    {
      key: 'channels',
      header: 'Số kênh',
      align: 'right',
      cell: (row) =>
        row.channel_count === 0 ? (
          <span className="text-muted">0</span>
        ) : (
          <Link
            to={`/channels?partner_id=${row.id}`}
            title={`Xem kênh của ${row.name}`}
            className="inline-flex items-center gap-1 font-medium text-blue underline-offset-4 hover:underline hover:decoration-blue"
          >
            <AtSign className="h-3.5 w-3.5" aria-hidden />
            {row.channel_count}
          </Link>
        ),
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

  return (
    <>
      <PageHeader
        icon={Handshake}
        title="Đối tác"
        description="Công ty và thương hiệu sở hữu các kênh TikTok bạn đang theo dõi."
        actions={
          canWrite ? (
            <Button variant="primary" onClick={() => setEditing('new')}>
              <Handshake className="h-4 w-4" aria-hidden />
              Thêm đối tác
            </Button>
          ) : null
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-4">
        <label className="relative w-full max-w-xs">
          <span className="sr-only">Tìm đối tác</span>
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" aria-hidden />
          <input
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Tìm theo tên hoặc ngành..."
            className="h-10 w-full rounded-field border border-border bg-card pl-8 pr-3 text-sm placeholder:text-muted focus:border-fg focus:outline-none"
          />
        </label>
        <CheckboxField label="Hiện đã lưu trữ" checked={archived} onChange={(e) => setArchived(e.target.checked)} />
        {data ? (
          <p role="status" className="ml-auto text-[13px] text-muted">
            {data.length} đối tác
          </p>
        ) : null}
        <RangePicker value={period} onChange={setPeriod} align="end" className={data ? undefined : 'ml-auto'} />
        <ViewToggle value={view} onChange={setView} />
      </div>

      <FormError message={actionError} />

      {view === 'cards' && data && data.length > 0 && !error ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
          {data.map((partner) => (
            <PartnerCard
              key={partner.id}
              partner={partner}
              channels={channelsByPartner.get(partner.id) ?? []}
              stats={statsByPartner.get(partner.id) ?? { followers: 0, growth: 0, views: 0, videos: 0, hasData: false }}
              periodText={periodLabel(period)}
              canWrite={canWrite}
              onEdit={setEditing}
              onToggleArchive={toggleArchive}
            />
          ))}
        </div>
      ) : (
      <Widget>
        {!data && loading ? (
          view === 'cards' ? (
            <div className="grid gap-4 p-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
              {Array.from({ length: 6 }, (_, i) => (
                <Skeleton key={i} className="h-80" />
              ))}
            </div>
          ) : (
            <div className="flex flex-col gap-2 p-4">
              {Array.from({ length: 5 }, (_, i) => (
                <Skeleton key={i} className="h-10" />
              ))}
            </div>
          )
        ) : error ? (
          <EmptyState
            icon={Handshake}
            title="Không tải được danh sách đối tác"
            description={errorMessage(error)}
            action={<Button variant="secondary" onClick={reload}>Thử lại</Button>}
          />
        ) : data && data.length === 0 ? (
          <EmptyState
            icon={Handshake}
            title={debounced ? 'Không tìm thấy đối tác' : 'Chưa có đối tác'}
            description={
              debounced
                ? `Không có đối tác nào khớp "${debounced}". Thử tên hoặc ngành khác.`
                : 'Đối tác là công ty hoặc thương hiệu sở hữu các kênh. Thêm đối tác đầu tiên rồi gắn kênh TikTok cho họ.'
            }
            action={
              canWrite && !debounced ? (
                <Button variant="secondary" onClick={() => setEditing('new')}>
                  <Handshake className="h-4 w-4" aria-hidden />
                  Thêm đối tác
                </Button>
              ) : undefined
            }
          />
        ) : (
          <DataTable columns={columns} rows={data ?? []} rowKey={(row) => row.id} caption="Danh sách đối tác" />
        )}
      </Widget>
      )}

      {editing ? (
        <PartnerDialog
          partner={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            reload();
          }}
        />
      ) : null}
    </>
  );
}
