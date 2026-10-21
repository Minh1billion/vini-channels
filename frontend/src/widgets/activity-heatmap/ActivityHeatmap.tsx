import { useEffect, useMemo, useRef, useState } from 'react';
import { localDay } from '@/shared/lib/period';
import { CELL, GAP, HEAT_CELL, HeatLegend, heatLevel, heatStyle } from './heat';

interface Props {
  counts: Record<string, number>;
  days?: number;
  unit?: string;
  ariaLabel: string;
}

const WEEKDAY_LABELS: Array<[number, string]> = [
  [0, 'T2'],
  [2, 'T4'],
  [4, 'T6'],
];

interface Cell {
  key: string;
  count: number;
  month: number;
  dayOfMonth: number;
}

const displayDay = (key: string) => key.split('-').reverse().join('/');

function buildColumns(counts: Record<string, number>, days: number): Array<Array<Cell | null>> {
  const cells: Cell[] = [];
  for (let offset = -(days - 1); offset <= 0; offset += 1) {
    const key = localDay(offset);
    const [, month, dayOfMonth] = key.split('-').map(Number);
    cells.push({ key, count: counts[key] ?? 0, month: month ?? 0, dayOfMonth: dayOfMonth ?? 0 });
  }
  const first = cells[0];
  const lead = first ? (new Date(`${first.key}T12:00:00`).getDay() + 6) % 7 : 0;
  const padded: Array<Cell | null> = [...Array.from({ length: lead }, () => null), ...cells];
  const columns: Array<Array<Cell | null>> = [];
  for (let index = 0; index < padded.length; index += 7) columns.push(padded.slice(index, index + 7));
  return columns;
}

export function ActivityHeatmap({ counts, days = 365, unit = 'video', ariaLabel }: Props) {
  const scroller = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState<Cell | null>(null);
  const columns = useMemo(() => buildColumns(counts, days), [counts, days]);
  const total = useMemo(() => columns.flat().reduce((sum, cell) => sum + (cell?.count ?? 0), 0), [columns]);
  const activeDays = useMemo(() => columns.flat().filter((cell) => cell && cell.count > 0).length, [columns]);
  const max = useMemo(() => Math.max(0, ...columns.flat().map((cell) => cell?.count ?? 0)), [columns]);

  useEffect(() => {
    const element = scroller.current;
    if (element) element.scrollLeft = element.scrollWidth;
  }, [columns]);

  const monthLabels = useMemo(() => {
    let previous = -1;
    return columns.map((column) => {
      const anchor = column.find((cell) => cell !== null) ?? null;
      if (!anchor || anchor.month === previous) return null;
      const startsHere = column.some((cell) => cell !== null && cell.dayOfMonth <= 7);
      if (!startsHere && previous !== -1) return null;
      previous = anchor.month;
      return `Th${anchor.month}`;
    });
  }, [columns]);

  const template = `repeat(${columns.length}, ${CELL}px)`;

  return (
    <figure className="flex flex-col gap-3">
      <figcaption className="min-h-[20px] text-sm">
        {active ? (
          <>
            <span className="font-medium">{displayDay(active.key)}</span>
            <span className="text-muted">
              {' '}
              · {active.count} {unit}
            </span>
          </>
        ) : (
          <span className="text-muted">
            <span className="font-medium text-fg">
              {total} {unit}
            </span>{' '}
            trong {days} ngày qua, đăng vào {activeDays} ngày. Rê chuột vào ô để xem chi tiết.
          </span>
        )}
      </figcaption>
      <div ref={scroller} className="overflow-x-auto pb-1">
        <div role="img" aria-label={ariaLabel} className="flex w-max gap-2" onMouseLeave={() => setActive(null)}>
          <div
            aria-hidden
            className="grid pt-[18px] text-[11px] leading-none text-muted"
            style={{ gridTemplateRows: `repeat(7, ${CELL}px)`, rowGap: GAP }}
          >
            {Array.from({ length: 7 }, (_, row) => (
              <span key={row} className="flex items-center">
                {WEEKDAY_LABELS.find(([index]) => index === row)?.[1] ?? ''}
              </span>
            ))}
          </div>
          <div className="flex flex-col gap-1">
            <div
              aria-hidden
              className="grid h-[14px] text-[11px] leading-none text-muted"
              style={{ gridTemplateColumns: template, columnGap: GAP }}
            >
              {monthLabels.map((label, index) => (
                <span key={index} className="whitespace-nowrap" style={{ gridColumn: index + 1 }}>
                  {label}
                </span>
              ))}
            </div>
            <div
              className="grid grid-flow-col"
              style={{
                gridTemplateColumns: template,
                gridTemplateRows: `repeat(7, ${CELL}px)`,
                gap: GAP,
              }}
            >
              {columns.flatMap((column, columnIndex) =>
                Array.from({ length: 7 }, (_, row) => {
                  const cell = column[row] ?? null;
                  if (!cell) return <span key={`${columnIndex}-${row}`} aria-hidden />;
                  return (
                    <span
                      key={cell.key}
                      onMouseEnter={() => setActive(cell)}
                      onClick={() => setActive(cell)}
                      className={HEAT_CELL}
                      style={heatStyle(heatLevel(cell.count, max), max >= 2 && cell.count === max, active?.key === cell.key)}
                    />
                  );
                }),
              )}
            </div>
          </div>
        </div>
      </div>
      <HeatLegend peakLabel="Ngày đăng nhiều nhất" />
    </figure>
  );
}
