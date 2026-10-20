import { useState, type MouseEvent } from 'react';
import { compact } from '@/shared/lib/format';

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
}

const WIDTH = 640;
const HEIGHT = 240;
const PAD = { left: 52, right: 12, top: 12, bottom: 28 };

const dayLabel = (iso: string) => {
  const [, month, day] = iso.split('-');
  return `${day}/${month}`;
};

export function CompareChart({ series, days, ariaLabel, format = compact, labelOf = dayLabel }: Props) {
  const [hover, setHover] = useState<number | null>(null);
  const all = series.flatMap((item) => Object.values(item.values));
  const min = Math.min(...all);
  const max = Math.max(...all);
  const span = max - min || Math.max(1, Math.abs(max) * 0.1);
  const lower = min - span * 0.1;
  const upper = max + span * 0.1;
  const innerWidth = WIDTH - PAD.left - PAD.right;
  const innerHeight = HEIGHT - PAD.top - PAD.bottom;
  const x = (index: number) =>
    PAD.left + (days.length === 1 ? innerWidth / 2 : (index / (days.length - 1)) * innerWidth);
  const y = (value: number) => PAD.top + (1 - (value - lower) / (upper - lower)) * innerHeight;
  const ticks = [lower + (upper - lower) * 0.1, (lower + upper) / 2, upper - (upper - lower) * 0.1];
  const active = hover === null ? days.length - 1 : hover;
  const activeDay = days[active];

  const path = (item: CompareSeries) =>
    days
      .map((day, index) => (day in item.values ? [index, item.values[day]] : null))
      .filter((point): point is [number, number] => point !== null)
      .map(([index, value], order) => `${order === 0 ? 'M' : 'L'}${x(index)},${y(value)}`)
      .join(' ');

  const onMove = (event: MouseEvent<SVGSVGElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    const ratio = ((event.clientX - box.left) / box.width) * WIDTH;
    const index = Math.round(((ratio - PAD.left) / innerWidth) * (days.length - 1));
    setHover(Math.min(days.length - 1, Math.max(0, index)));
  };

  return (
    <figure className="flex flex-col gap-3">
      <figcaption className="flex flex-wrap items-baseline gap-x-4 gap-y-1 text-sm">
        <span className="text-muted">{labelOf(activeDay)}</span>
        {series.map((item) => (
          <span key={item.name} className="inline-flex items-center gap-1.5">
            <SeriesSwatch color={item.color} dash={item.dash} />
            <span className="text-muted">{item.name}</span>
            <span className="font-medium">{activeDay in item.values ? format(item.values[activeDay]) : '—'}</span>
          </span>
        ))}
      </figcaption>
      <svg
        role="img"
        aria-label={ariaLabel}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        className="h-auto w-full"
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
      >
        {ticks.map((tick) => (
          <g key={tick}>
            <line x1={PAD.left} x2={WIDTH - PAD.right} y1={y(tick)} y2={y(tick)} stroke="var(--border)" />
            <text x={PAD.left - 8} y={y(tick) + 4} textAnchor="end" fontSize="11" fill="var(--muted)">
              {compact(tick)}
            </text>
          </g>
        ))}
        <line x1={x(active)} x2={x(active)} y1={PAD.top} y2={PAD.top + innerHeight} stroke="var(--border)" />
        {series.map((item) => (
          <g key={item.name}>
            <path d={path(item)} fill="none" stroke={item.color} strokeDasharray={item.dash} strokeWidth="2" strokeLinejoin="round" />
            {activeDay in item.values ? (
              <circle cx={x(active)} cy={y(item.values[activeDay])} r="4" fill={item.color} stroke="var(--card)" strokeWidth="2" />
            ) : null}
          </g>
        ))}
        <text x={PAD.left} y={HEIGHT - 8} fontSize="11" fill="var(--muted)">
          {labelOf(days[0])}
        </text>
        {days.length > 1 ? (
          <text x={WIDTH - PAD.right} y={HEIGHT - 8} textAnchor="end" fontSize="11" fill="var(--muted)">
            {labelOf(days[days.length - 1])}
          </text>
        ) : null}
      </svg>
    </figure>
  );
}
