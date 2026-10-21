import { ExternalLink } from 'lucide-react';
import { useMemo, useState, type MouseEvent } from 'react';
import { median } from '@/entities/analytics/insights';
import type { VideoRecord } from '@/entities/analytics/types';
import { niceScale } from '@/shared/lib/chartScale';
import { clock, compact, dateTime, percent, shortDate } from '@/shared/lib/format';
import { useChartWidth } from '@/shared/lib/useChartWidth';
import { Chip } from '@/shared/ui';
import { SeriesSwatch } from '@/widgets/compare-chart/CompareChart';

type XMode = 'posted' | 'duration';
type YMode = 'views' | 'erv';

interface Dot {
  video: VideoRecord;
  x: number;
  y: number;
}

interface Tick {
  value: number;
  label: string;
}

const HEIGHT = 330;
const PAD = { left: 72, right: 14, top: 14, bottom: 52 };
const WEEK = 7 * 24 * 3600 * 1000;
const DAY = 24 * 3600 * 1000;

const yValue = (video: VideoRecord, mode: YMode) => (mode === 'views' ? video.views : (video.erv ?? 0));

export function VideoScatter({ videos }: { videos: VideoRecord[] }) {
  const [xMode, setXMode] = useState<XMode>('posted');
  const [yMode, setYMode] = useState<YMode>('views');
  const [log, setLog] = useState(false);
  const [trendline, setTrendline] = useState(true);
  const [hover, setHover] = useState<number | null>(null);
  const [pinned, setPinned] = useState<number | null>(null);
  const [figureRef, width] = useChartWidth<HTMLElement>();

  const useLog = log && yMode === 'views';
  const showTrend = trendline && xMode === 'posted';

  const dots = useMemo<Dot[]>(
    () =>
      videos
        .filter((video) => (xMode === 'duration' ? video.duration_sec > 0 : true) && (yMode === 'views' || video.erv !== null))
        .map((video) => ({
          video,
          x: xMode === 'posted' ? new Date(video.posted_at).getTime() : video.duration_sec,
          y: yValue(video, yMode),
        })),
    [videos, xMode, yMode],
  );

  const innerWidth = width - PAD.left - PAD.right;
  const innerHeight = HEIGHT - PAD.top - PAD.bottom;

  const layout = useMemo(() => {
    if (dots.length === 0) return null;
    const xs = dots.map((dot) => dot.x);
    const ys = dots.map((dot) => dot.y);
    let xLow = Math.min(...xs);
    let xHigh = Math.max(...xs);
    if (xMode === 'posted') {
      const pad = Math.max(DAY / 2, (xHigh - xLow) * 0.03);
      xLow -= pad;
      xHigh += pad;
    } else {
      const scale = niceScale(0, xHigh, { zeroBased: true, targetTicks: 5 });
      xLow = scale.lower;
      xHigh = scale.upper;
    }
    const xTicks: Tick[] =
      xMode === 'posted'
        ? [0, 1, 2, 3].map((step) => {
            const value = xLow + ((xHigh - xLow) * step) / 3;
            return { value, label: shortDate(new Date(value)) };
          })
        : niceScale(0, xHigh, { zeroBased: true, targetTicks: 5 }).ticks.map((value) => ({ value, label: clock(value) }));

    let yTicks: Tick[];
    let yTransform: (value: number) => number;
    let yLow: number;
    let yHigh: number;
    if (useLog) {
      yTransform = (value) => Math.log10(Math.max(1, value));
      yLow = 0;
      yHigh = Math.max(1, Math.ceil(yTransform(Math.max(...ys))));
      yTicks = Array.from({ length: yHigh + 1 }, (_, power) => ({ value: power, label: compact(10 ** power) }));
    } else {
      const scale = niceScale(0, Math.max(...ys), { zeroBased: true });
      yTransform = (value) => value;
      yLow = scale.lower;
      yHigh = scale.upper;
      yTicks = scale.ticks.map((value) => ({ value, label: yMode === 'views' ? compact(value) : percent(value, 1) }));
    }
    return { xLow, xHigh, xTicks, yLow, yHigh, yTicks, yTransform };
  }, [dots, xMode, yMode, useLog]);

  if (!layout) {
    return (
      <figure ref={figureRef} className="flex flex-col gap-3">
        <p className="rounded-field bg-surface px-4 py-6 text-center text-sm text-muted">
          Không có video phù hợp với cách xem này. Hãy đổi trục ngang hoặc trục dọc.
        </p>
        <button type="button" className="self-center text-[13px] text-blue underline-offset-4 hover:underline" onClick={() => { setXMode('posted'); setYMode('views'); }}>
          Về cách xem mặc định
        </button>
      </figure>
    );
  }

  const { xLow, xHigh, xTicks, yLow, yHigh, yTicks, yTransform } = layout;
  const px = (value: number) => PAD.left + ((value - xLow) / (xHigh - xLow || 1)) * innerWidth;
  const py = (value: number) => PAD.top + (1 - (yTransform(value) - yLow) / (yHigh - yLow || 1)) * innerHeight;
  const tickY = (value: number) => PAD.top + (1 - (value - yLow) / (yHigh - yLow || 1)) * innerHeight;

  const typical = median(dots.map((dot) => dot.y));
  const isOutlier = (dot: Dot) => typical !== null && typical > 0 && dot.y >= typical * 3;
  const outliers = dots.filter(isOutlier).length;

  const weekly: Array<[number, number]> = [];
  if (showTrend) {
    const origin = Math.min(...dots.map((dot) => dot.x));
    const groups = new Map<number, Dot[]>();
    for (const dot of dots) {
      const key = Math.floor((dot.x - origin) / WEEK);
      groups.set(key, [...(groups.get(key) ?? []), dot]);
    }
    for (const key of [...groups.keys()].sort((a, b) => a - b)) {
      const members = groups.get(key) ?? [];
      const centre = members.reduce((sum, dot) => sum + dot.x, 0) / members.length;
      weekly.push([centre, median(members.map((dot) => dot.y)) ?? 0]);
    }
  }

  const nearest = (event: MouseEvent<SVGSVGElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    const sx = ((event.clientX - box.left) / box.width) * width;
    const sy = ((event.clientY - box.top) / box.height) * HEIGHT;
    let best: number | null = null;
    let bestDistance = 22;
    dots.forEach((dot, index) => {
      const distance = Math.hypot(px(dot.x) - sx, py(dot.y) - sy);
      if (distance < bestDistance) {
        best = index;
        bestDistance = distance;
      }
    });
    return best;
  };

  const activeIndex = hover ?? pinned;
  const active = activeIndex !== null && activeIndex < dots.length ? dots[activeIndex] : null;
  const yFormat = yMode === 'views' ? compact : (value: number) => percent(value, 1);
  const xTitle = xMode === 'posted' ? 'Ngày đăng' : 'Thời lượng video (phút:giây)';
  const yTitle = yMode === 'views' ? (useLog ? 'Lượt xem (thang log)' : 'Lượt xem') : 'Tỉ lệ tương tác (ERV)';

  return (
    <figure ref={figureRef} className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
        <div role="group" aria-label="Trục ngang" className="flex items-center gap-1.5 text-[13px] text-muted">
          Trục ngang
          <Chip active={xMode === 'posted'} onClick={() => setXMode('posted')}>
            Ngày đăng
          </Chip>
          <Chip active={xMode === 'duration'} onClick={() => setXMode('duration')}>
            Thời lượng
          </Chip>
        </div>
        <div role="group" aria-label="Trục dọc" className="flex items-center gap-1.5 text-[13px] text-muted">
          Trục dọc
          <Chip active={yMode === 'views'} onClick={() => setYMode('views')}>
            Lượt xem
          </Chip>
          <Chip active={yMode === 'erv'} onClick={() => setYMode('erv')}>
            Tương tác
          </Chip>
        </div>
        {yMode === 'views' ? (
          <Chip active={log} onClick={() => setLog((value) => !value)}>
            Thang log
          </Chip>
        ) : null}
        {xMode === 'posted' ? (
          <Chip active={trendline} onClick={() => setTrendline((value) => !value)}>
            Trung vị theo tuần
          </Chip>
        ) : null}
      </div>

      <figcaption className="flex min-h-[44px] flex-col gap-1 text-sm">
        {active ? (
          <>
            <span className="flex items-center gap-2">
              <span className="truncate font-medium">{active.video.caption || active.video.platform_video_id}</span>
              {active.video.url ? (
                <a
                  href={active.video.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex shrink-0 items-center gap-1 text-[13px] text-blue underline-offset-4 hover:underline"
                >
                  Mở video
                  <ExternalLink className="h-3.5 w-3.5" aria-hidden />
                </a>
              ) : null}
            </span>
            <span className="text-[13px] text-muted">
              {dateTime(new Date(active.video.posted_at))} · {compact(active.video.views)} lượt xem · tương tác{' '}
              {percent(active.video.erv)} · {active.video.duration_sec > 0 ? clock(active.video.duration_sec) : 'không rõ thời lượng'}
            </span>
          </>
        ) : (
          <span className="text-[13px] text-muted">
            Rê chuột vào một điểm để xem chi tiết, bấm để ghim. Mỗi điểm là một video, đo ở lần đồng bộ gần nhất.
          </span>
        )}
      </figcaption>

      <svg
        role="img"
        aria-label={`Biểu đồ phân tán ${dots.length} video`}
        viewBox={`0 0 ${width} ${HEIGHT}`}
        width={width}
        height={HEIGHT}
        className="block max-w-full"
        style={{ cursor: hover !== null ? 'pointer' : 'default' }}
        onMouseMove={(event) => setHover(nearest(event))}
        onMouseLeave={() => setHover(null)}
        onClick={(event) => setPinned(nearest(event))}
      >
        {yTicks.map((tick) => (
          <g key={tick.value}>
            <line x1={PAD.left} x2={width - PAD.right} y1={tickY(tick.value)} y2={tickY(tick.value)} stroke="var(--border)" />
            <text x={PAD.left - 8} y={tickY(tick.value) + 4} textAnchor="end" fontSize="11" fill="var(--muted)">
              {tick.label}
            </text>
          </g>
        ))}
        {xTicks.map((tick) => (
          <text key={tick.value} x={px(tick.value)} y={HEIGHT - 28} textAnchor="middle" fontSize="11" fill="var(--muted)">
            {tick.label}
          </text>
        ))}
        <text
          transform={`translate(13 ${PAD.top + innerHeight / 2}) rotate(-90)`}
          textAnchor="middle"
          fontSize="11"
          fill="var(--muted)"
        >
          {yTitle}
        </text>
        <text x={PAD.left + innerWidth / 2} y={HEIGHT - 6} textAnchor="middle" fontSize="11" fill="var(--muted)">
          {xTitle}
        </text>
        {active ? (
          <g stroke="var(--muted)" strokeDasharray="3 3" opacity="0.7">
            <line x1={PAD.left} x2={px(active.x)} y1={py(active.y)} y2={py(active.y)} />
            <line x1={px(active.x)} x2={px(active.x)} y1={py(active.y)} y2={PAD.top + innerHeight} />
          </g>
        ) : null}
        {typical !== null ? (
          <line x1={PAD.left} x2={width - PAD.right} y1={py(typical)} y2={py(typical)} stroke="var(--muted)" strokeWidth="2.5" strokeDasharray="7 4" />
        ) : null}
        {weekly.length > 1 ? (
          <path
            d={weekly.map(([x, y], index) => `${index === 0 ? 'M' : 'L'}${px(x)},${py(y)}`).join(' ')}
            fill="none"
            stroke="var(--fg)"
            strokeWidth="2"
            strokeLinejoin="round"
          />
        ) : null}
        {dots.map((dot, index) => (
          <circle
            key={dot.video.id}
            cx={px(dot.x)}
            cy={py(dot.y)}
            r={index === activeIndex ? 6 : 4}
            fill={isOutlier(dot) ? 'var(--red)' : 'var(--blue)'}
            fillOpacity={index === activeIndex || isOutlier(dot) ? 1 : 0.65}
            stroke={index === activeIndex ? 'var(--fg)' : 'var(--card)'}
            strokeWidth={index === activeIndex ? 2 : 1}
          />
        ))}
      </svg>

      <p className="flex flex-wrap items-center gap-x-5 gap-y-1 text-[13px] text-muted">
        <span className="inline-flex items-center gap-1.5">
          <SeriesSwatch color="var(--muted)" dash="7 4" />
          Trung vị {typical === null ? '—' : yFormat(typical)}
        </span>
        {weekly.length > 1 ? (
          <span className="inline-flex items-center gap-1.5">
            <SeriesSwatch color="var(--fg)" />
            Trung vị theo tuần đăng
          </span>
        ) : null}
        {outliers > 0 ? (
          <span className="inline-flex items-center gap-1.5">
            <span aria-hidden className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: 'var(--red)' }} />
            Nổi bật: từ 3 lần trung vị trở lên ({outliers} video)
          </span>
        ) : null}
        {xMode === 'posted' ? <span>Video đăng sớm đã có nhiều thời gian tích luỹ lượt xem hơn video mới.</span> : null}
      </p>
    </figure>
  );
}
