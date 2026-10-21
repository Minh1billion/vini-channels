import { useState, type MouseEvent } from 'react';
import { niceScale } from '@/shared/lib/chartScale';
import { compact } from '@/shared/lib/format';
import { useChartWidth } from '@/shared/lib/useChartWidth';

export interface CompareSeries {
  name: string;
  color: string;
  dash?: string;
  values: Record<string, number>;
}

export const SERIES_STYLES: Array<{ color: string; dash?: string }> = [
  { color: 'var(--fg)' },
  { color: 'var(--blue)' },
  { color: 'var(--fg)', dash: '6 4' },
  { color: 'var(--blue)', dash: '6 4' },
  { color: 'var(--muted)', dash: '2 3' },
];

export const seriesStyle = (index: number) => SERIES_STYLES[index % SERIES_STYLES.length];

export function SeriesSwatch({ color, dash }: { color: string; dash?: string }) {
  return (
    <svg width="16" height="8" aria-hidden className="shrink-0">
      <line x1="0" x2="16" y1="4" y2="4" stroke={color} strokeWidth="2.5" strokeDasharray={dash} />
    </svg>
  );
}

interface Props {
  series: CompareSeries[];
  days: string[];
  ariaLabel: string;
  format?: (value: number) => string;
  labelOf?: (key: string) => string;
  zeroBased?: boolean;
  xValue?: (key: string) => number;
  singlePointHint?: string;
  xTitle?: string;
  yTitle?: string;
}

const BASE_PAD = { left: 60, right: 12, top: 12, bottom: 28 };

const dayLabel = (iso: string) => {
  const [, month, day] = iso.split('-');
  return `${day}/${month}`;
};

export function CompareChart({
  series,
  days,
  ariaLabel,
  format = compact,
  labelOf = dayLabel,
  zeroBased = false,
  xValue,
  singlePointHint = 'Mới có một điểm dữ liệu cho mỗi đường. Biểu đồ sẽ xuất hiện sau khi đồng bộ thêm.',
  xTitle,
  yTitle,
}: Props) {
  const [hover, setHover] = useState<number | null>(null);
  const [figureRef, width] = useChartWidth<HTMLElement>();
  const HEIGHT = xTitle ? 264 : 240;
  const PAD = { ...BASE_PAD, left: yTitle ? 76 : BASE_PAD.left, bottom: xTitle ? 52 : BASE_PAD.bottom };
  const labelY = xTitle ? HEIGHT - 28 : HEIGHT - 8;
  const all = series.flatMap((item) => Object.values(item.values));
  const hasLine = series.some((item) => Object.keys(item.values).length > 1);
  const latest = days.length - 1;
  const active = hover === null ? latest : hover;
  const activeDay = days[active];

  const legend = (key: string) => (
    <figcaption className="flex flex-wrap items-baseline gap-x-4 gap-y-1 text-sm">
      <span className="text-muted">{labelOf(key)}</span>
      {series.map((item) => (
        <span key={item.name} className="inline-flex items-center gap-1.5">
          <SeriesSwatch color={item.color} dash={item.dash} />
          <span className="text-muted">{item.name}</span>
          <span className="font-medium">{key in item.values ? format(item.values[key]) : '—'}</span>
        </span>
      ))}
    </figcaption>
  );

  if (!hasLine) {
    return (
      <figure ref={figureRef} className="flex flex-col gap-3">
        {legend(activeDay)}
        <p className="rounded-field bg-surface px-4 py-6 text-center text-sm text-muted">{singlePointHint}</p>
      </figure>
    );
  }

  const { lower, upper, ticks } = niceScale(Math.min(...all), Math.max(...all), { zeroBased });
  const positions = days.map((day, index) => (xValue ? xValue(day) : index));
  const first = positions[0];
  const last = positions[positions.length - 1];
  const innerWidth = width - PAD.left - PAD.right;
  const innerHeight = HEIGHT - PAD.top - PAD.bottom;
  const x = (index: number) => PAD.left + (last === first ? 0 : ((positions[index] - first) / (last - first)) * innerWidth);
  const y = (value: number) => PAD.top + (1 - (value - lower) / (upper - lower)) * innerHeight;

  const points = (item: CompareSeries) =>
    days
      .map((day, index) => (day in item.values ? ([index, item.values[day]] as [number, number]) : null))
      .filter((point): point is [number, number] => point !== null);

  const path = (item: CompareSeries) =>
    points(item)
      .map(([index, value], order) => `${order === 0 ? 'M' : 'L'}${x(index)},${y(value)}`)
      .join(' ');

  const onMove = (event: MouseEvent<SVGSVGElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    const position = ((event.clientX - box.left) / box.width) * width;
    let nearest = 0;
    for (let index = 1; index < days.length; index += 1) {
      if (Math.abs(x(index) - position) < Math.abs(x(nearest) - position)) nearest = index;
    }
    setHover(nearest);
  };

  return (
    <figure ref={figureRef} className="flex flex-col gap-3">
      {legend(activeDay)}
      <svg
        role="img"
        aria-label={ariaLabel}
        viewBox={`0 0 ${width} ${HEIGHT}`}
        width={width}
        height={HEIGHT}
        className="block max-w-full"
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
      >
        {ticks.map((tick) => (
          <g key={tick}>
            <line x1={PAD.left} x2={width - PAD.right} y1={y(tick)} y2={y(tick)} stroke="var(--border)" />
            <text x={PAD.left - 8} y={y(tick) + 4} textAnchor="end" fontSize="11" fill="var(--muted)">
              {format(tick)}
            </text>
          </g>
        ))}
        <line x1={x(active)} x2={x(active)} y1={PAD.top} y2={PAD.top + innerHeight} stroke="var(--border)" />
        {series.map((item) => (
          <g key={item.name}>
            <path d={path(item)} fill="none" stroke={item.color} strokeDasharray={item.dash} strokeWidth="2" strokeLinejoin="round" />
            {points(item).length <= 31
              ? points(item).map(([index, value]) => (
                  <circle key={index} cx={x(index)} cy={y(value)} r="2.5" fill={item.color} />
                ))
              : null}
            {activeDay in item.values ? (
              <circle cx={x(active)} cy={y(item.values[activeDay])} r="9" fill={item.color} opacity="0.15" />
            ) : null}
            {activeDay in item.values ? (
              <circle cx={x(active)} cy={y(item.values[activeDay])} r="4" fill={item.color} stroke="var(--card)" strokeWidth="2" />
            ) : null}
          </g>
        ))}
        <text x={PAD.left} y={labelY} fontSize="11" fill="var(--muted)">
          {labelOf(days[0])}
        </text>
        <text x={width - PAD.right} y={labelY} textAnchor="end" fontSize="11" fill="var(--muted)">
          {labelOf(days[days.length - 1])}
        </text>
        {yTitle ? (
          <text
            transform={`translate(13 ${PAD.top + innerHeight / 2}) rotate(-90)`}
            textAnchor="middle"
            fontSize="11"
            fill="var(--muted)"
          >
            {yTitle}
          </text>
        ) : null}
        {xTitle ? (
          <text x={PAD.left + innerWidth / 2} y={HEIGHT - 6} textAnchor="middle" fontSize="11" fill="var(--muted)">
            {xTitle}
          </text>
        ) : null}
      </svg>
    </figure>
  );
}
