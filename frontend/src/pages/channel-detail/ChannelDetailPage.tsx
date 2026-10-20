import { ArrowLeft, ExternalLink, LineChart, RefreshCw } from 'lucide-react';
import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import type { VideoGrowth } from '@/entities/analytics/types';
import { changeRatio, signedCount, signedPercent, type Kpi } from '@/entities/analytics/kpis';
import { ChannelAvatar } from '@/entities/channel/ChannelAvatar';
import { StatusBadge } from '@/entities/channel/StatusBadge';
import { toneFor } from '@/entities/channel/tone';
import { SourceTag } from '@/entities/provider/ProviderLogo';
import { SyncStatusBadge } from '@/entities/sync/SyncStatusBadge';
import type { SyncRunRecord } from '@/entities/sync/types';
import { useAuth } from '@/features/auth/AuthProvider';
import { analyticsApi, channelsApi, syncApi } from '@/shared/api';
import { RangePicker } from '@/features/period-picker/RangePicker';
import { errorMessage } from '@/shared/lib/errors';
import { lastDays, periodKey, periodLabel, type Period } from '@/shared/lib/period';
import { compact, dateTime, full, percent, relativeTime } from '@/shared/lib/format';
import { useAsync } from '@/shared/lib/useAsync';
import { Button, DataTable, EmptyState, FormError, Skeleton, Widget, type Column } from '@/shared/ui';
import { KpiRow } from '@/widgets/kpi-row/KpiRow';
import { PageHeader } from '@/widgets/page-header/PageHeader';
import { TrendChart } from '@/widgets/trend-chart/TrendChart';
import { CompareChart, seriesStyle } from '@/widgets/compare-chart/CompareChart';
import { VideoGrid } from '@/widgets/video-grid/VideoGrid';

const METRICS = [
  { id: 'followers', label: 'Người theo dõi' },
  { id: 'total_likes', label: 'Tổng lượt thích' },
] as const;

type MetricId = (typeof METRICS)[number]['id'];

const dayLabel = (iso: string) => {
  const [, month, day] = iso.split('-');
  return `${day}/${month}`;
};


const growthColumns: Array<Column<VideoGrowth>> = [
  {
    key: 'video',
    header: 'Video',
    cell: (v) => <span className="block max-w-[320px] truncate">{v.caption || v.platform_video_id}</span>,
  },
  { key: 'posted', header: 'Đăng lúc', cell: (v) => dateTime(new Date(v.posted_at)) },
  { key: 'h24', header: 'Sau 24 giờ', align: 'right', cell: (v) => compact(v.views_24h) },
  { key: 'h72', header: 'Sau 72 giờ', align: 'right', cell: (v) => compact(v.views_72h) },
  { key: 'views', header: 'Hiện tại', align: 'right', cell: (v) => compact(v.views) },
];

const runColumns: Array<Column<SyncRunRecord>> = [
  { key: 'status', header: 'Trạng thái', cell: (r) => <SyncStatusBadge status={r.status} /> },
  { key: 'source', header: 'Nguồn', cell: (r) => <SourceTag source={r.source} /> },
  { key: 'trigger', header: 'Kích hoạt', cell: (r) => (r.trigger === 'manual' ? 'Thủ công' : 'Theo lịch') },
  { key: 'items', header: 'Bản ghi', align: 'right', cell: (r) => full(r.items_fetched) },
  {
    key: 'started',
    header: 'Bắt đầu',
    cell: (r) => (
      <time dateTime={r.started_at} title={dateTime(new Date(r.started_at))}>
        {relativeTime(new Date(r.started_at))}
      </time>
    ),
  },
  {
    key: 'error',
    header: 'Lỗi',
    cell: (r) => <span className="block max-w-[260px] truncate text-muted">{r.error_message ?? '—'}</span>,
  },
];

export function ChannelDetailPage() {
  const { id = '' } = useParams();
  const { can } = useAuth();
  const canReadSync = can('sync:read');
  const canSync = can('sync:write');
  const [period, setPeriod] = useState<Period>(lastDays(30));
  const [metric, setMetric] = useState<MetricId>('followers');
  const [syncing, setSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const periodId = periodKey(period);

  const channel = useAsync(() => channelsApi.get(id), [id]);
  const metrics = useAsync(() => analyticsApi.metrics(id, period), [id, periodId]);
  const trend = useAsync(() => analyticsApi.trend(id, period), [id, periodId]);
  const daily = useAsync(() => analyticsApi.dailyViews(id, period), [id, periodId]);
  const growth = useAsync(() => analyticsApi.videoGrowth(id, period), [id, periodId]);
  const top = useAsync(() => analyticsApi.videos({ channel_id: id, period, sort: 'views', limit: 6 }), [id, periodId]);
  const runs = useAsync(
    () => (canReadSync ? syncApi.runs({ channel_id: id, limit: 10 }) : Promise.resolve([])),
    [id, canReadSync],
  );

  const reloadAll = () => {
    channel.reload();
    metrics.reload();
    trend.reload();
    daily.reload();
    growth.reload();
    top.reload();
    runs.reload();
  };

  const syncNow = async () => {
    setSyncing(true);
    setSyncError(null);
    try {
      await syncApi.syncChannel(id);
    } catch (err) {
      setSyncError(errorMessage(err));
    } finally {
      setSyncing(false);
      reloadAll();
    }
  };

  if (channel.error) {
    return (
      <>
        <PageHeader
        icon={LineChart}
        title="Chi tiết kênh"
        description="Hiệu quả và video của kênh theo thời gian."
      />
        <Widget>
          <EmptyState
            icon={LineChart}
            title="Không tải được kênh"
            description={errorMessage(channel.error)}
            action={
              <Link to="/channels">
                <Button variant="secondary">Về danh sách kênh</Button>
              </Link>
            }
          />
        </Widget>
      </>
    );
  }

  const record = channel.data;
  const points = trend.data ?? [];
  const latest = points.length > 0 ? points[points.length - 1] : null;
  const data = metrics.data;
  const kpis: Kpi[] | undefined = data
    ? [
        {
          label: 'Người theo dõi',
          value: latest ? compact(latest.followers) : '—',
          delta: signedCount(data.current.follower_growth),
          deltaValue: data.current.follower_growth,
          hint: `trong ${data.days} ngày`,
        },
        {
          label: 'Lượt xem',
          value: compact(data.current.total_views),
          delta: signedPercent(changeRatio(data.current.total_views, data.previous.total_views)),
          deltaValue: changeRatio(data.current.total_views, data.previous.total_views),
          hint: 'so với kỳ trước',
        },
        {
          label: 'Tỉ lệ tương tác',
          value: percent(data.current.erv),
          delta: signedPercent(data.erv_change),
          deltaValue: data.erv_change,
          hint: 'so với kỳ trước',
        },
        {
          label: 'Video đã đăng',
          value: full(data.current.video_count),
          delta: signedPercent(changeRatio(data.current.video_count, data.previous.video_count)),
          deltaValue: changeRatio(data.current.video_count, data.previous.video_count),
          hint: 'so với kỳ trước',
        },
      ]
    : undefined;

  return (
    <>
      <Link to="/channels" className="mb-3 inline-flex items-center gap-1.5 text-sm text-muted hover:text-fg">
        <ArrowLeft className="h-4 w-4" aria-hidden />
        Kênh
      </Link>
      <PageHeader
        icon={LineChart}
        description="Hiệu quả và video của kênh theo thời gian."
        title={record ? record.display_name || `@${record.handle}` : 'Chi tiết kênh'}
        actions={
          record ? (
            <>
              <a href={`https://www.tiktok.com/@${record.handle}`} target="_blank" rel="noreferrer">
                <Button variant="secondary">
                  <ExternalLink className="h-4 w-4" aria-hidden />
                  Mở TikTok
                </Button>
              </a>
              {canSync && record.is_active && !record.archived_at ? (
                <Button variant="primary" disabled={syncing} onClick={syncNow}>
                  <RefreshCw className="h-4 w-4" aria-hidden />
                  {syncing ? 'Đang đồng bộ...' : 'Đồng bộ ngay'}
                </Button>
              ) : null}
            </>
          ) : null
        }
      />

      {record ? (
        <div className="-mt-3 mb-5 flex flex-wrap items-center gap-3 text-sm text-muted">
          <ChannelAvatar name={record.display_name || record.handle} tone={toneFor(record.id)} src={record.avatar_url} size={32} />
          <span className="font-mono">@{record.handle}</span>
          <StatusBadge status={record.status} />
        </div>
      ) : (
        <Skeleton className="mb-5 h-8 w-64" />
      )}

      <FormError message={syncError} />

      <div className="mb-4">
        <RangePicker value={period} onChange={setPeriod} />
      </div>

      <div className="flex flex-col gap-6">
        {metrics.error ? (
          <FormError message={errorMessage(metrics.error)} />
        ) : (
          <KpiRow items={kpis} />
        )}

        <Widget
          title="Xu hướng"
          actions={
            <span className="flex gap-1 pr-1">
              {METRICS.map((item) => (
                <Button
                  key={item.id}
                  size="sm"
                  variant={metric === item.id ? 'accent' : 'ghost'}
                  aria-pressed={metric === item.id}
                  onClick={() => setMetric(item.id)}
                >
                  {item.label}
                </Button>
              ))}
            </span>
          }
          bodyClassName="p-4"
        >
          {!trend.data && trend.loading ? (
            <Skeleton className="h-[220px]" />
          ) : trend.error ? (
            <EmptyState
              icon={LineChart}
              title="Không tải được xu hướng"
              description={errorMessage(trend.error)}
              action={<Button variant="secondary" onClick={trend.reload}>Thử lại</Button>}
            />
          ) : points.length === 0 ? (
            <EmptyState icon={LineChart} title="Chưa có dữ liệu" description="Đồng bộ kênh để có số liệu theo ngày." />
          ) : (
            <TrendChart
              points={points.map((point) => ({ label: dayLabel(point.day), value: point[metric] }))}
              ariaLabel={`Biểu đồ ${METRICS.find((item) => item.id === metric)?.label.toLowerCase()} ${periodLabel(period)}`}
              format={full}
            />
          )}
        </Widget>

        <Widget title="Lượt xem theo ngày" bodyClassName="p-4">
          {!daily.data && daily.loading ? (
            <Skeleton className="h-[220px]" />
          ) : daily.error ? (
            <EmptyState
              icon={LineChart}
              title="Không tải được lượt xem theo ngày"
              description={errorMessage(daily.error)}
              action={<Button variant="secondary" onClick={daily.reload}>Thử lại</Button>}
            />
          ) : !daily.data || daily.data.every((point) => point.views === 0) ? (
            <EmptyState icon={LineChart} title="Chưa có dữ liệu" description="Cần ít nhất hai lần đồng bộ để tính lượt xem mỗi ngày." />
          ) : (
            <TrendChart
              points={daily.data.map((point) => ({ label: dayLabel(point.day), value: point.views }))}
              ariaLabel={`Biểu đồ lượt xem theo ngày ${periodLabel(period)}`}
              format={full}
            />
          )}
        </Widget>

        <Widget title="Tăng trưởng video" bodyClassName="p-4">
          {!growth.data && growth.loading ? (
            <Skeleton className="h-[240px]" />
          ) : growth.error ? (
            <EmptyState
              icon={LineChart}
              title="Không tải được tăng trưởng video"
              description={errorMessage(growth.error)}
              action={<Button variant="secondary" onClick={growth.reload}>Thử lại</Button>}
            />
          ) : !growth.data || growth.data.length === 0 ? (
            <EmptyState icon={LineChart} title="Chưa có dữ liệu" description="Chưa có video đăng trong kỳ này có số liệu." />
          ) : (
            <div className="flex flex-col gap-4">
              <CompareChart
                series={growth.data.map((video, index) => ({
                  name: video.caption.slice(0, 24) || video.platform_video_id,
                  ...seriesStyle(index),
                  values: Object.fromEntries(video.curve.map((point) => [String(point.age_days), point.views])),
                }))}
                days={Array.from(new Set(growth.data.flatMap((video) => video.curve.map((point) => String(point.age_days)))))
                  .sort((a, b) => Number(a) - Number(b))}
                labelOf={(key) => `Ngày ${key}`}
                ariaLabel="Đường tăng trưởng lượt xem của các video theo số ngày sau khi đăng"
                format={full}
              />
              <DataTable caption="Lượt xem video sau 24 và 72 giờ" columns={growthColumns} rows={growth.data} rowKey={(v) => v.video_id} />
            </div>
          )}
        </Widget>

        <section>
          <div className="mb-3 flex items-center justify-between gap-2">
            <h2 className="text-base font-bold">Video nổi bật</h2>
            <Link to="/videos" className="text-sm font-medium text-blue underline-offset-4 hover:underline hover:decoration-blue">
              Xem tất cả video
            </Link>
          </div>
          <VideoGrid videos={top.data} />
        </section>

        {canReadSync ? (
          <Widget title="Lịch sử đồng bộ">
            {!runs.data && runs.loading ? (
              <Skeleton className="h-[160px]" />
            ) : runs.data && runs.data.length === 0 ? (
              <EmptyState icon={RefreshCw} title="Chưa có lần đồng bộ nào" description="Bấm Đồng bộ ngay để lấy dữ liệu đầu tiên." />
            ) : (
              <DataTable caption="Lịch sử đồng bộ của kênh" columns={runColumns} rows={runs.data ?? []} rowKey={(r) => r.id} />
            )}
          </Widget>
        ) : null}
      </div>
    </>
  );
}
