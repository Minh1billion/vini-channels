import { LineChart, Scale } from 'lucide-react';
import { useState } from 'react';
import { signedCount, signedPercent } from '@/entities/analytics/kpis';
import type { ChannelMetrics, MetricsValues } from '@/entities/analytics/types';
import { analyticsApi, channelsApi } from '@/shared/api';
import { RangePicker } from '@/features/period-picker/RangePicker';
import { errorMessage } from '@/shared/lib/errors';
import { compact, full, percent } from '@/shared/lib/format';
import { lastDays, periodKey, periodLabel, type Period } from '@/shared/lib/period';
import { useAsync } from '@/shared/lib/useAsync';
import { Button, Chip, DataTable, EmptyState, FormError, Skeleton, Widget, type Column } from '@/shared/ui';
import { CompareChart, SeriesSwatch, seriesStyle, type CompareSeries } from '@/widgets/compare-chart/CompareChart';
import { PageHeader } from '@/widgets/page-header/PageHeader';

const MIN_CHANNELS = 2;
const MAX_CHANNELS = 5;

const TREND_METRICS = [
  { id: 'followers', label: 'Người theo dõi' },
  { id: 'total_likes', label: 'Tổng lượt thích' },
] as const;

type TrendMetric = (typeof TREND_METRICS)[number]['id'];

interface MetricRow {
  key: string;
  label: string;
  value: (values: MetricsValues) => string;
}

const ROWS: MetricRow[] = [
  { key: 'follower_growth', label: 'Tăng trưởng người theo dõi', value: (v) => signedCount(v.follower_growth) },
  { key: 'follower_growth_ratio', label: 'Tăng trưởng (%)', value: (v) => signedPercent(v.follower_growth_ratio) ?? '—' },
  { key: 'video_count', label: 'Video đã đăng', value: (v) => full(v.video_count) },
  { key: 'total_views', label: 'Tổng lượt xem', value: (v) => compact(v.total_views) },
  { key: 'average_views', label: 'Lượt xem trung bình', value: (v) => compact(v.average_views) },
  { key: 'median_views', label: 'Lượt xem trung vị', value: (v) => compact(v.median_views) },
  { key: 'total_likes', label: 'Lượt thích', value: (v) => compact(v.total_likes) },
  { key: 'total_comments', label: 'Bình luận', value: (v) => compact(v.total_comments) },
  { key: 'total_shares', label: 'Chia sẻ', value: (v) => compact(v.total_shares) },
  { key: 'erv', label: 'Tỉ lệ tương tác', value: (v) => percent(v.erv) },
  { key: 'posts_per_week', label: 'Bài đăng mỗi tuần', value: (v) => (v.posts_per_week === null ? '—' : v.posts_per_week.toFixed(1).replace('.', ',')) },
];

export function ComparePage() {
  const [selected, setSelected] = useState<string[]>([]);
  const [period, setPeriod] = useState<Period>(lastDays(30));
  const [trendMetric, setTrendMetric] = useState<TrendMetric>('followers');
  const periodId = periodKey(period);
  const ready = selected.length >= MIN_CHANNELS;
  const key = selected.join(',');

  const channels = useAsync(() => channelsApi.list(), []);
  const compare = useAsync(
    () => (ready ? analyticsApi.compare(selected, period) : Promise.resolve(null)),
    [key, periodId],
  );
  const trends = useAsync(
    () => (ready ? Promise.all(selected.map((id) => analyticsApi.trend(id, period))) : Promise.resolve(null)),
    [key, periodId],
  );

  const options = channels.data ?? [];
  const nameOf = (id: string) => {
    const channel = options.find((item) => item.id === id);
    return channel ? channel.display_name || `@${channel.handle}` : id;
  };

  const toggle = (id: string) =>
    setSelected((current) => {
      if (current.includes(id)) return current.filter((item) => item !== id);
      return current.length >= MAX_CHANNELS ? current : [...current, id];
    });

  const results = compare.data?.channels ?? [];
  const columns: Array<Column<MetricRow>> = [
    { key: 'metric', header: 'Chỉ số', cell: (row) => row.label },
    ...results.map((item: ChannelMetrics, index) => ({
      key: item.channel_id,
      header: (
        <span className="inline-flex items-center gap-1.5">
          <SeriesSwatch {...seriesStyle(index)} />
          {nameOf(item.channel_id)}
        </span>
      ),
      align: 'right' as const,
      cell: (row: MetricRow) => row.value(item.current),
    })),
  ];

  const trendData = trends.data ?? [];
  const chartDays = Array.from(new Set(trendData.flatMap((points) => points.map((point) => point.day)))).sort();
  const series: CompareSeries[] = trendData.map((points, index) => ({
    name: nameOf(selected[index]),
    ...seriesStyle(index),
    values: Object.fromEntries(points.map((point) => [point.day, point[trendMetric]])),
  }));

  return (
    <>
      <PageHeader
        icon={Scale}
        title="So sánh"
        description="Đặt nhiều kênh cạnh nhau để so sánh các chỉ số theo thời gian."
      />

      <div className="flex flex-col gap-6">
        <Widget
          title={`Chọn kênh (${selected.length}/${MAX_CHANNELS})`}
          actions={
            selected.length > 0 ? (
              <Button size="sm" variant="ghost" onClick={() => setSelected([])}>
                Bỏ chọn
              </Button>
            ) : undefined
          }
          bodyClassName="flex flex-col gap-3 p-4"
        >
          {channels.error ? (
            <FormError message={errorMessage(channels.error)} />
          ) : !channels.data ? (
            <Skeleton className="h-8" />
          ) : (
            <div className="flex flex-wrap gap-2">
              {options.map((channel) => {
                const active = selected.includes(channel.id);
                return (
                  <Chip
                    key={channel.id}
                    active={active}
                    tone="red"
                    onClick={!active && selected.length >= MAX_CHANNELS ? undefined : () => toggle(channel.id)}
                  >
                    {channel.display_name || `@${channel.handle}`}
                  </Chip>
                );
              })}
            </div>
          )}
          <p className="text-sm text-muted">
            Chọn từ {MIN_CHANNELS} đến {MAX_CHANNELS} kênh.
          </p>
          <RangePicker value={period} onChange={setPeriod} />
        </Widget>

        {!ready ? (
          <Widget>
            <EmptyState
              icon={Scale}
              title="Chọn ít nhất 2 kênh"
              description="Số liệu và biểu đồ so sánh sẽ hiện ở đây."
            />
          </Widget>
        ) : (
          <>
            <Widget title="Chỉ số cạnh nhau">
              {compare.error ? (
                <div className="p-4">
                  <FormError message={errorMessage(compare.error)} />
                </div>
              ) : !compare.data ? (
                <Skeleton className="h-[240px]" />
              ) : (
                <DataTable caption="So sánh chỉ số các kênh" columns={columns} rows={ROWS} rowKey={(row) => row.key} />
              )}
            </Widget>

            <Widget
              title="Xu hướng"
              actions={
                <span className="flex gap-1 pr-1">
                  {TREND_METRICS.map((item) => (
                    <Button
                      key={item.id}
                      size="sm"
                      variant={trendMetric === item.id ? 'accent' : 'ghost'}
                      aria-pressed={trendMetric === item.id}
                      onClick={() => setTrendMetric(item.id)}
                    >
                      {item.label}
                    </Button>
                  ))}
                </span>
              }
              bodyClassName="p-4"
            >
              {trends.error ? (
                <FormError message={errorMessage(trends.error)} />
              ) : !trends.data ? (
                <Skeleton className="h-[240px]" />
              ) : chartDays.length === 0 ? (
                <EmptyState icon={LineChart} title="Chưa có dữ liệu" description="Đồng bộ các kênh để có số liệu theo ngày." />
              ) : (
                <CompareChart
                  series={series}
                  days={chartDays}
                  ariaLabel={`Biểu đồ so sánh ${TREND_METRICS.find((item) => item.id === trendMetric)?.label.toLowerCase()} ${periodLabel(period)}`}
                  format={full}
                />
              )}
            </Widget>
          </>
        )}
      </div>
    </>
  );
}
