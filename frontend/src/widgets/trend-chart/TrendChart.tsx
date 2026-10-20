import { useState, type MouseEvent } from 'react';
import { compact } from '@/shared/lib/format';

export interface TrendDatum {
  label: string;
  value: number;
}

interface Props {
  points: TrendDatum[];
  ariaLabel: string;
  format?: (value: number) => string;
}

const WIDTH = 640;
const HEIGHT = 220;
const PAD = { left: 52, right: 12, top: 12, bottom: 28 };

export function TrendChart({ points, ariaLabel, format = compact }: Props) {
  const [hover, setHover] = useState<number | null>(null);
  const values = points.map((point) => point.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || Math.max(1, Math.abs(max) * 0.1);
  const lower = min - span * 0.1;
  const upper = max + span * 0.1;
  const innerWidth = WIDTH - PAD.left - PAD.right;
  const innerHeight = HEIGHT - PAD.top - PAD.bottom;
  const x = (index: number) =>
    PAD.left + (points.length === 1 ? innerWidth / 2 : (index / (points.length - 1)) * innerWidth);
  const y = (value: number) => PAD.top + (1 - (value - lower) / (upper - lower)) * innerHeight;
  const line = points.map((point, index) => `${index === 0 ? 'M' : 'L'}${x(index)},${y(point.value)}`).join(' ');
  const area = `${line} L${x(points.length - 1)},${PAD.top + innerHeight} L${x(0)},${PAD.top + innerHeight} Z`;
  const ticks = [lower + (upper - lower) * 0.1, (lower + upper) / 2, upper - (upper - lower) * 0.1];
  const active = hover === null ? points.length - 1 : hover;

  const onMove = (event: MouseEvent<SVGSVGElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    const ratio = ((event.clientX - box.left) / box.width) * WIDTH;
    const index = Math.round(((ratio - PAD.left) / innerWidth) * (points.length - 1));
    setHover(Math.min(points.length - 1, Math.max(0, index)));
  };

  return (
    <figure className="flex flex-col gap-2">
      <figcaption className="flex items-baseline justify-between gap-3 text-sm">
        <span className="text-muted">{points[active].label}</span>
        <span className="font-medium">{format(points[active].value)}</span>
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
        {points.length > 1 ? (
          <>
            <path d={area} fill="var(--blue)" opacity="0.12" />
            <path d={line} fill="none" stroke="var(--blue)" strokeWidth="2" strokeLinejoin="round" />
          </>
        ) : null}
        <circle cx={x(active)} cy={y(points[active].value)} r="4" fill="var(--blue)" stroke="var(--card)" strokeWidth="2" />
        <text x={PAD.left} y={HEIGHT - 8} fontSize="11" fill="var(--muted)">
          {points[0].label}
        </text>
        {points.length > 1 ? (
          <text x={WIDTH - PAD.right} y={HEIGHT - 8} textAnchor="end" fontSize="11" fill="var(--muted)">
            {points[points.length - 1].label}
          </text>
        ) : null}
      </svg>
    </figure>
  );
}
