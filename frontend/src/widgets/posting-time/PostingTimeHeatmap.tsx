import { useMemo, useState } from 'react';
import { WEEKDAYS, WEEKDAY_NAMES, hourRange, postingSlots, slotAverage, type Slot } from '@/entities/analytics/insights';
import type { VideoRecord } from '@/entities/analytics/types';
import { compact } from '@/shared/lib/format';
import { Chip } from '@/shared/ui';
import { CELL, GAP, HEAT_CELL, HeatLegend, heatLevel, heatStyle } from '@/widgets/activity-heatmap/heat';

type Metric = 'count' | 'average';

const valueOf = (slot: Slot, metric: Metric) => (metric === 'count' ? slot.count : slotAverage(slot));
const sameSlot = (a: Slot | null, b: Slot) => a !== null && a.weekday === b.weekday && a.hour === b.hour;

const detail = (slot: Slot) =>
  `${slot.count} video${slot.count > 0 ? ` · TB ${compact(slotAverage(slot))} lượt xem` : ''}`;

export function PostingTimeHeatmap({ videos }: { videos: VideoRecord[] }) {
  const [metric, setMetric] = useState<Metric>('average');
  const [active, setActive] = useState<Slot | null>(null);

  const grid = useMemo(() => postingSlots(videos), [videos]);
  const ranked = useMemo(
    () =>
      grid
        .flat()
        .filter((slot) => slot.count > 0)
        .sort((a, b) => valueOf(b, metric) - valueOf(a, metric) || b.count - a.count),
    [grid, metric],
  );
  const max = ranked.length > 0 ? valueOf(ranked[0], metric) : 0;
  const isPeak = (slot: Slot) => max > 0 && valueOf(slot, metric) === max && (metric === 'average' || max >= 2);
  const top = ranked.slice(0, 3);

  return (
    <figure className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <figcaption className="min-h-[20px] text-sm">
          {active ? (
            <>
              <span className="font-medium">
                {WEEKDAY_NAMES[active.weekday]}, {hourRange(active.hour)}
              </span>
              <span className="text-muted"> · {detail(active)}</span>
            </>
          ) : (
            <span className="text-muted">
              <span className="font-medium text-fg">{videos.length} video</span> theo giờ địa phương của trình duyệt. Rê chuột vào ô để xem chi tiết.
            </span>
          )}
        </figcaption>
        <div role="group" aria-label="Chỉ số hiển thị" className="flex gap-1.5">
          <Chip active={metric === 'average'} onClick={() => setMetric('average')}>
            Lượt xem TB
          </Chip>
          <Chip active={metric === 'count'} onClick={() => setMetric('count')}>
            Số video
          </Chip>
        </div>
      </div>

      <div className="flex flex-wrap items-start gap-x-10 gap-y-4">
        <div className="max-w-full overflow-x-auto pb-1">
          <div
            role="img"
            aria-label="Bản đồ nhiệt thời điểm đăng video theo thứ và giờ"
            className="grid w-max text-[11px] leading-none text-muted"
            style={{ gridTemplateColumns: `auto repeat(24, ${CELL}px)`, gap: GAP, columnGap: GAP }}
            onMouseLeave={() => setActive(null)}
          >
            <span aria-hidden className="pr-2">
              Thứ
            </span>
            {Array.from({ length: 24 }, (_, hour) => (
              <span key={hour} aria-hidden className="whitespace-nowrap text-center">
                {hour % 3 === 0 ? hour : ''}
              </span>
            ))}
            {grid.map((row, weekday) => (
              <div key={weekday} className="contents">
                <span aria-hidden className="flex items-center pr-2" style={{ height: CELL }}>
                  {WEEKDAYS[weekday]}
                </span>
                {row.map((slot) => (
                  <span
                    key={slot.hour}
                    onMouseEnter={() => setActive(slot)}
                    onClick={() => setActive(slot)}
                    className={HEAT_CELL}
                    style={{
                      height: CELL,
                      ...heatStyle(heatLevel(valueOf(slot, metric), max), isPeak(slot), sameSlot(active, slot)),
                    }}
                  />
                ))}
              </div>
            ))}
          </div>
          <p className="mt-2 text-[11px] text-muted">Giờ trong ngày (0–23h)</p>
        </div>

        {top.length > 0 ? (
          <aside aria-label="Khung giờ nổi bật" className="flex min-w-[220px] flex-1 flex-col gap-2">
            <h3 className="text-[13px] font-bold uppercase tracking-wide text-muted">Khung giờ nổi bật</h3>
            <ol className="flex flex-col gap-1.5">
              {top.map((slot, index) => (
                <li
                  key={`${slot.weekday}-${slot.hour}`}
                  onMouseEnter={() => setActive(slot)}
                  onMouseLeave={() => setActive(null)}
                  className="flex cursor-pointer items-center gap-3 rounded-field border border-border px-3 py-2 text-sm transition duration-150 hover:-translate-y-0.5 hover:border-blue hover:bg-surface"
                >
                  <span
                    aria-hidden
                    className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold"
                    style={
                      index === 0
                        ? { backgroundColor: 'var(--red)', color: 'var(--on-red)' }
                        : { backgroundColor: 'var(--surface)', color: 'var(--fg)' }
                    }
                  >
                    {index + 1}
                  </span>
                  <span className="flex min-w-0 flex-col">
                    <span className="truncate font-medium">
                      {WEEKDAY_NAMES[slot.weekday]}, {hourRange(slot.hour)}
                    </span>
                    <span className="text-[12px] text-muted">{detail(slot)}</span>
                  </span>
                </li>
              ))}
            </ol>
          </aside>
        ) : null}
      </div>

      <HeatLegend peakLabel={metric === 'average' ? 'Khung giờ hiệu quả nhất' : 'Khung giờ đăng nhiều nhất'} />
    </figure>
  );
}
