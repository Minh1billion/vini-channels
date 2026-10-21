import { useState, type MouseEvent } from 'react';
import { signedCount, signedPercent } from '@/entities/analytics/kpis';
import { niceScale } from '@/shared/lib/chartScale';
import { compact } from '@/shared/lib/format';
import { useChartWidth } from '@/shared/lib/useChartWidth';

export interface TrendDatum {
  label: string;
  value: number;
}

interface Props {
  points: TrendDatum[];
  ariaLabel: string;
  format?: (value: number) => string;
  zeroBased?: boolean;
  showChange?: boolean;
  xTitle?: string;
  yTitle?: string;
}

const BASE_PAD = { left: 60, right: 12, top: 12, bottom: 28 };

export function TrendChart({ points, ariaLabel, format = compact, zeroBased = false, showChange = false, xTitle, yTitle }: Props) {
  const [hover, setHover] = useState<number | null>(null);
  const [figureRef, width] = useChartWidth<HTMLElement>();
  const HEIGHT = xTitle ? 244 : 220;
  const PAD = { ...BASE_PAD, left: yTitle ? 76 : BASE_PAD.left, bottom: xTitle ? 52 : BASE_PAD.bottom };
  const labelY = xTitle ? HEIGHT - 28 : HEIGHT - 8;

  if (points.length === 1) {
    return (
      <figure ref={figureRef} className="flex flex-col items-center gap-1 py-8 text-center">
        <span className="text-sm text-muted">{points[0].label}</span>
        <span className="text-3xl font-semibold">{format(points[0].value)}</span>
        <figcaption className="mt-2 max-w-sm text-sm text-muted">
          Mới có dữ liệu của một ngày. Biểu đồ xu hướng sẽ xuất hiện sau khi đồng bộ thêm ít nhất một ngày nữa.
        </figcaption>
      </figure>
    );
  }

  const values = points.map((point) => point.value);
  const { lower, upper, ticks } = niceScale(Math.min(...values), Math.max(...values), { zeroBased });
  const innerWidth = width - PAD.left - PAD.right;
  const innerHeight = HEIGHT - PAD.top - PAD.bottom;
  const x = (index: number) => PAD.left + (index / (points.length - 1)) * innerWidth;
  const y = (value: number) => PAD.top + (1 - (value - lower) / (upper - lower)) * innerHeight;
  const line = points.map((point, index) => `${index === 0 ? 'M' : 'L'}${x(index)},${y(point.value)}`).join(' ');
  const area = `${line} L${x(points.length - 1)},${PAD.top + innerHeight} L${x(0)},${PAD.top + innerHeight} Z`;
  const active = hover === null ? points.length - 1 : hover;
  const peakIndex = Math.max(...values) > Math.min(...values) && points.length > 2 ? values.indexOf(Math.max(...values)) : -1;
  const peakX = peakIndex >= 0 ? x(peakIndex) : 0;
  const peakAnchor = peakX < PAD.left + 40 ? 'start' : peakX > width - PAD.right - 40 ? 'end' : 'middle';
  const change = points[active].value - points[0].value;
  const ratio = points[0].value !== 0 ? change / points[0].value : null;
  const ratioText = signedPercent(ratio);

  const onMove = (event: MouseEvent<SVGSVGElement>) => {
    const box = event.currentTarget.getBoundingClientRect();
    const position = ((event.clientX - box.left) / box.width) * width;
    const index = Math.round(((position - PAD.left) / innerWidth) * (points.length - 1));
    setHover(Math.min(points.length - 1, Math.max(0, index)));
  };

  return (
    <figure ref={figureRef} className="flex flex-col gap-2">
      <figcaption className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1 text-sm">
        <span className="text-muted">{points[active].label}</span>
        <span className="flex items-baseline gap-3">
          {showChange && active > 0 ? (
            <span className={change > 0 ? 'text-up' : change < 0 ? 'text-down' : 'text-muted'}>
              {signedCount(change)}
              {ratioText ? ` (${ratioText})` : ''} so với {points[0].label}
            </span>
          ) : null}
          <span className="font-medium">{format(points[active].value)}</span>
        </span>
      </figcaption>
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
        <path d={area} fill="var(--blue)" opacity="0.12" />
        <path d={line} fill="none" stroke="var(--blue)" strokeWidth="2" strokeLinejoin="round" />
        {points.length <= 31
          ? points.map((point, index) => (
              <circle key={point.label + index} cx={x(index)} cy={y(point.value)} r="2.5" fill="var(--blue)" />
            ))
          : null}
        <line x1={x(active)} x2={x(active)} y1={PAD.top} y2={PAD.top + innerHeight} stroke="var(--border)" />
        {peakIndex >= 0 && peakIndex !== active ? (
          <g>
            <circle cx={peakX} cy={y(values[peakIndex])} r="4.5" fill="var(--red)" stroke="var(--card)" strokeWidth="2" />
            <text x={peakX} y={y(values[peakIndex]) - 10} textAnchor={peakAnchor} fontSize="11" fontWeight="600" fill="var(--red)">
              {format(values[peakIndex])}
            </text>
          </g>
        ) : null}
        <circle cx={x(active)} cy={y(points[active].value)} r="9" fill={active === peakIndex ? 'var(--red)' : 'var(--blue)'} opacity="0.18" />
        <circle cx={x(active)} cy={y(points[active].value)} r="4" fill={active === peakIndex ? 'var(--red)' : 'var(--blue)'} stroke="var(--card)" strokeWidth="2" />
        <text x={PAD.left} y={labelY} fontSize="11" fill="var(--muted)">
          {points[0].label}
        </text>
        <text x={width - PAD.right} y={labelY} textAnchor="end" fontSize="11" fill="var(--muted)">
          {points[points.length - 1].label}
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
