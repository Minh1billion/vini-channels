import type { CSSProperties } from 'react';

export const CELL = 16;
export const GAP = 3;

const OPACITY = [0, 0.3, 0.55, 0.8, 1];

export const HEAT_CELL =
  'cursor-pointer rounded-[3px] bg-surface shadow-[inset_0_0_0_1px_var(--border)] transition-transform duration-100 hover:relative hover:z-10 hover:scale-125';

export const heatLevel = (value: number, max: number) =>
  value <= 0 || max <= 0 ? 0 : Math.max(1, Math.ceil((value / max) * (OPACITY.length - 1)));

export function heatStyle(level: number, peak: boolean, selected: boolean): CSSProperties | undefined {
  const ring = '0 0 0 2px var(--fg)';
  if (level === 0) return selected ? { boxShadow: ring } : undefined;
  return {
    backgroundColor: peak ? 'var(--red)' : 'var(--blue)',
    opacity: peak ? 1 : OPACITY[level],
    boxShadow: selected ? ring : 'none',
  };
}

export function HeatLegend({ peakLabel }: { peakLabel: string }) {
  return (
    <div className="flex flex-wrap items-center justify-end gap-x-4 gap-y-1 text-[11px] text-muted" aria-hidden>
      <span className="flex items-center gap-1.5">
        <span>Ít</span>
        {OPACITY.map((opacity, level) => (
          <span
            key={level}
            className="rounded-[3px] bg-surface shadow-[inset_0_0_0_1px_var(--border)]"
            style={{
              width: 12,
              height: 12,
              ...(level > 0 ? { backgroundColor: 'var(--blue)', opacity, boxShadow: 'none' } : {}),
            }}
          />
        ))}
        <span>Nhiều</span>
      </span>
      <span className="flex items-center gap-1.5">
        <span className="rounded-[3px]" style={{ width: 12, height: 12, backgroundColor: 'var(--red)' }} />
        {peakLabel}
      </span>
    </div>
  );
}
