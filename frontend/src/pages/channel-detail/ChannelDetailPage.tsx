import { Activity, ArrowLeft, Check, Clapperboard, Copy, ExternalLink, LineChart, RefreshCw, TrendingUp } from 'lucide-react';
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { channelFacts } from '@/entities/analytics/insights';
import type { VideoGrowth, VideoRecord, VideoSort } from '@/entities/analytics/types';
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
import { Button, Chip, DataTable, EmptyState, FormError, Skeleton, Tabs, Widget, type Column } from '@/shared/ui';
import { MetricGrid, type Profile } from '@/widgets/channel-metrics/MetricGrid';
import { DataReadiness, NeedsBadge } from '@/widgets/data-readiness/DataReadiness';
import { EngagementMix } from '@/widgets/engagement-mix/EngagementMix';
import { KpiRow } from '@/widgets/kpi-row/KpiRow';
import { PageHeader } from '@/widgets/page-header/PageHeader';
import { PostingTimeHeatmap } from '@/widgets/posting-time/PostingTimeHeatmap';
import { TrendChart } from '@/widgets/trend-chart/TrendChart';
import { ActivityHeatmap } from '@/widgets/activity-heatmap/ActivityHeatmap';
import { CompareChart, seriesStyle } from '@/widgets/compare-chart/CompareChart';
import { VideoGrid } from '@/widgets/video-grid/VideoGrid';
import { VideoScatter } from '@/widgets/video-scatter/VideoScatter';
import { ViewsDistribution } from '@/widgets/views-distribution/ViewsDistribution';

const METRICS = [
  { id: 'followers', label: 'Người theo dõi' },
  { id: 'total_likes', label: 'Tổng lượt thích' },
  { id: 'video_count', label: 'Số video' },
] as const;

type MetricId = (typeof METRICS)[number]['id'];
type TrendMode = 'total' | 'change';
type TabId = 'state' | 'trend' | 'videos';

const TABS: Array<{ id: TabId; label: string; icon: typeof Activity }> = [
  { id: 'state', label: 'Hiện trạng', icon: Activity },
  { id: 'trend', label: 'Xu hướng', icon: TrendingUp },
  { id: 'videos', label: 'Video và đồng bộ', icon: Clapperboard },
];

const TOP_SORTS: Array<{ id: VideoSort; label: string }> = [
  { id: 'views', label: 'Lượt xem' },
  { id: 'likes', label: 'Lượt thích' },
  { id: 'comments', label: 'Bình luận' },
  { id: 'shares', label: 'Chia sẻ' },
  { id: 'erv', label: 'Tương tác' },
];

const metricTitle = (id: MetricId) => METRICS.find((item) => item.id === id)?.label ?? '';

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

const HEATMAP_DAYS = 365;

export function ChannelDetailPage() {
  const { id = '' } = useParams();
  const [searchParams] = useSearchParams();
  const targetVideoId = searchParams.get('video');
  const { can } = useAuth();
  const canReadSync = can('sync:read');
  const canSync = can('sync:write');
  const [period, setPeriod] = useState<Period>(targetVideoId ? { kind: 'all' } : lastDays(30));
  const [metric, setMetric] = useState<MetricId>('followers');
  const [mode, setMode] = useState<TrendMode>('total');
  const [tab, setTab] = useState<TabId>(targetVideoId ? 'videos' : 'state');
  const [topSort, setTopSort] = useState<VideoSort>('views');
  const [syncing, setSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const periodId = periodKey(period);

  const channel = useAsync(() => channelsApi.get(id), [id]);
  const metrics = useAsync(() => analyticsApi.metrics(id, period), [id, periodId]);
  const trend = useAsync(() => analyticsApi.trend(id, period), [id, periodId]);
  const daily = useAsync(() => analyticsApi.dailyViews(id, period), [id, periodId]);
  const posting = useAsync(() => analyticsApi.postingActivity(id, lastDays(HEATMAP_DAYS)), [id]);
  const postingCounts = useMemo(
    () => Object.fromEntries((posting.data ?? []).map((item) => [item.day, item.count])),
    [posting.data],
  );
  const growth = useAsync(() => analyticsApi.videoGrowth(id, period), [id, periodId]);
  const top = useAsync(() => analyticsApi.videos({ channel_id: id, period, sort: topSort, limit: 6 }), [id, periodId, topSort]);
  const videosAll = useAsync(
    () => analyticsApi.videoPage({ channel_id: id, period, sort: 'posted', limit: 200 }),
    [id, periodId],
  );
  const facts = useMemo(() => (videosAll.data ? channelFacts(videosAll.data.items) : null), [videosAll.data]);
  const targetVideo = useMemo(
    () => (targetVideoId ? videosAll.data?.items.find((item) => item.id === targetVideoId) ?? null : null),
    [targetVideoId, videosAll.data],
  );
  const targetRef = useRef<HTMLElement>(null);
  useEffect(() => {
    if (tab === 'videos' && targetVideo) targetRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, [tab, targetVideo]);
  const runs = useAsync(
    () => (canReadSync ? syncApi.runs({ channel_id: id, limit: 10 }) : Promise.resolve([])),
    [id, canReadSync],
  );

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(`${window.location.origin}/channels/${id}`);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  };

  const reloadAll = () => {
    channel.reload();
    metrics.reload();
    trend.reload();
    daily.reload();
    growth.reload();
    posting.reload();
    top.reload();
    videosAll.reload();
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
  const profile: Profile | null = latest
    ? { followers: latest.followers, totalLikes: latest.total_likes, videoCount: latest.video_count }
    : null;
  const hasCurve = growth.data && growth.data.length > 0 ? growth.data.some((video) => video.curve.length > 1) : undefined;
  const trendSeries = points.map((point) => ({ label: dayLabel(point.day), value: point[metric] }));
  const trendShown =
    mode === 'change' ? trendSeries.slice(1).map((point, index) => ({ ...point, value: point.value - trendSeries[index].value })) : trendSeries;
  const metricLabel = METRICS.find((item) => item.id === metric)?.label.toLowerCase();

  const withVideos = (skeleton: string, render: (videos: VideoRecord[]) => ReactNode): ReactNode => {
    if (videosAll.error) {
      return (
        <EmptyState
          icon={LineChart}
          title="Không tải được danh sách video"
          description={errorMessage(videosAll.error)}
          action={<Button variant="secondary" onClick={videosAll.reload}>Thử lại</Button>}
        />
      );
    }
    if (!videosAll.data) return <Skeleton className={skeleton} />;
    if (videosAll.data.items.length === 0) {
      return <EmptyState icon={Clapperboard} title="Chưa có video" description="Đồng bộ kênh để lấy video và số liệu của lần đầu tiên." />;
    }
    return render(videosAll.data.items);
  };
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
              <Button variant="secondary" onClick={copyLink}>
                {copied ? <Check className="h-4 w-4" aria-hidden /> : <Copy className="h-4 w-4" aria-hidden />}
                {copied ? 'Đã sao chép' : 'Sao chép liên kết'}
              </Button>
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
          <Link to={`/channels?partner_id=${record.partner_id}`} className="text-blue underline-offset-4 hover:underline">
            Kênh cùng đối tác
          </Link>
          <Link to={`/videos?channel_id=${record.id}`} className="text-blue underline-offset-4 hover:underline">
            Tất cả video
          </Link>
        </div>
      ) : (
        <Skeleton className="mb-5 h-8 w-64" />
      )}

      <FormError message={syncError} />

      <div className="mb-4">
        <RangePicker value={period} onChange={setPeriod} />
      </div>

      <div className="flex flex-col gap-6">
        <DataReadiness syncDays={trend.data ? trend.data.length : undefined} videoCount={videosAll.data?.total} hasCurve={hasCurve} />

        {metrics.error ? <FormError message={errorMessage(metrics.error)} /> : <KpiRow items={kpis} />}

        <Tabs tabs={TABS} value={tab} onChange={setTab} label="Nhóm biểu đồ của kênh" />

        {tab === 'state' ? (
          <div role="tabpanel" id="panel-state" aria-labelledby="tab-state" className="flex flex-col gap-6">
            <MetricGrid data={data} facts={facts} profile={profile} />

            <Widget title="Hiệu quả từng video" actions={<NeedsBadge kind="single" />} bodyClassName="p-4">
              {withVideos('h-[380px]', (videos) => (
                <VideoScatter videos={videos} />
              ))}
            </Widget>

            <div className="grid gap-6 lg:grid-cols-2">
              <Widget title="Phân bố lượt xem" actions={<NeedsBadge kind="single" />} bodyClassName="p-4">
                {withVideos('h-[300px]', (videos) => (
                  <ViewsDistribution videos={videos} />
                ))}
              </Widget>
              <Widget title="Cơ cấu tương tác" actions={<NeedsBadge kind="single" />} bodyClassName="p-4">
                {data ? (
                  <EngagementMix
                    likes={data.current.total_likes}
                    comments={data.current.total_comments}
                    shares={data.current.total_shares}
                    saves={facts?.saves ?? null}
                    views={data.current.total_views}
                  />
                ) : (
                  <Skeleton className="h-[300px]" />
                )}
              </Widget>
            </div>

            <Widget title="Thời điểm đăng hiệu quả" actions={<NeedsBadge kind="single" />} bodyClassName="p-4">
              {withVideos('h-[220px]', (videos) => (
                <PostingTimeHeatmap videos={videos} />
              ))}
            </Widget>

            <Widget title="Tần suất đăng video" actions={<NeedsBadge kind="single" />} bodyClassName="p-4">
              {!posting.data && posting.loading ? (
                <Skeleton className="h-[150px]" />
              ) : posting.error ? (
                <EmptyState
                  icon={LineChart}
                  title="Không tải được tần suất đăng video"
                  description={errorMessage(posting.error)}
                  action={<Button variant="secondary" onClick={posting.reload}>Thử lại</Button>}
                />
              ) : (
                <ActivityHeatmap
                  counts={postingCounts}
                  days={HEATMAP_DAYS}
                  ariaLabel={`Biểu đồ tần suất đăng video ${HEATMAP_DAYS} ngày qua`}
                />
              )}
            </Widget>

            {videosAll.data && videosAll.data.total > videosAll.data.items.length ? (
              <p className="text-[13px] text-muted">
                Các biểu đồ video dựa trên {videosAll.data.items.length} video mới nhất trong tổng số {full(videosAll.data.total)} video của kỳ này.
              </p>
            ) : null}
          </div>
        ) : null}

        {tab === 'trend' ? (
          <div role="tabpanel" id="panel-trend" aria-labelledby="tab-trend" className="flex flex-col gap-6">
            <Widget
              title="Xu hướng kênh"
              actions={
                <span className="flex flex-wrap items-center gap-1 pr-1">
                  <NeedsBadge kind="multi" />
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
              bodyClassName="flex flex-col gap-3 p-4"
            >
              <div role="group" aria-label="Cách hiển thị" className="flex gap-1.5">
                <Chip active={mode === 'total'} onClick={() => setMode('total')}>
                  Giá trị theo ngày
                </Chip>
                <Chip active={mode === 'change'} onClick={() => setMode('change')}>
                  Thay đổi so với ngày trước
                </Chip>
              </div>
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
              ) : trendShown.length === 0 ? (
                <EmptyState icon={LineChart} title="Cần thêm dữ liệu" description="Thay đổi theo ngày cần số liệu của ít nhất hai ngày." />
              ) : (
                <TrendChart
                  points={trendShown}
                  ariaLabel={`Biểu đồ ${metricLabel} ${periodLabel(period)}`}
                  format={mode === 'change' ? signedCount : full}
                  showChange={mode === 'total'}
                  zeroBased={mode === 'change'}
                  xTitle="Ngày"
                  yTitle={mode === 'change' ? `${metricTitle(metric)} (thay đổi mỗi ngày)` : metricTitle(metric)}
                />
              )}
            </Widget>

            <Widget title="Lượt xem theo ngày" actions={<NeedsBadge kind="multi" />} bodyClassName="p-4">
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
                  zeroBased
                  xTitle="Ngày"
                  yTitle="Lượt xem phát sinh trong ngày"
                />
              )}
            </Widget>

            <Widget title="Tăng trưởng video" actions={<NeedsBadge kind="multi" />} bodyClassName="p-4">
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
                    zeroBased
                    xTitle="Số ngày sau khi đăng"
                    yTitle="Lượt xem tích luỹ"
                    xValue={Number}
                    singlePointHint="Mỗi video mới có một lần ghi nhận lượt xem. Cần đồng bộ thêm vào các ngày khác nhau để thấy đường tăng trưởng."
                  />
                  <DataTable caption="Lượt xem video sau 24 và 72 giờ" columns={growthColumns} rows={growth.data} rowKey={(v) => v.video_id} />
                </div>
              )}
            </Widget>
          </div>
        ) : null}

        {tab === 'videos' ? (
          <div role="tabpanel" id="panel-videos" aria-labelledby="tab-videos" className="flex flex-col gap-6">
            {targetVideo ? (
              <section ref={targetRef} aria-label="Video được tìm thấy" className="animate-rise">
                <h2 className="mb-3 text-base font-bold">Video bạn đã tìm</h2>
                <div className="max-w-[220px] rounded-card ring-2 ring-blue ring-offset-2 ring-offset-bg">
                  <VideoGrid videos={[targetVideo]} single />
                </div>
              </section>
            ) : null}

            <section>
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h2 className="text-base font-bold">Video nổi bật</h2>
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-[13px] text-muted">Xếp theo</span>
                  {TOP_SORTS.map((item) => (
                    <Chip key={item.id} active={topSort === item.id} onClick={() => setTopSort(item.id)}>
                      {item.label}
                    </Chip>
                  ))}
                  <Link to={`/videos?channel_id=${id}`} className="ml-2 text-sm font-medium text-blue underline-offset-4 hover:underline hover:decoration-blue">
                    Xem tất cả video
                  </Link>
                </div>
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
        ) : null}
      </div>
    </>
  );
}
