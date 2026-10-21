import { useMemo, useState } from 'react';
import { median, viewBuckets } from '@/entities/analytics/insights';
import type { VideoRecord } from '@/entities/analytics/types';
import { niceScale } from '@/shared/lib/chartScale';
import { compact, percent, shortDate } from '@/shared/lib/format';
import { useChartWidth } from '@/shared/lib/useChartWidth';
import { SeriesSwatch } from '@/widgets/compare-chart/CompareChart';

const HEIGHT = 250;
const PAD = { left: 56, right: 8, top: 16, bottom: 52 };
const VIRAL = 3;

export function ViewsDistribution({ videos }: { videos: VideoRecord[] }) {
  const [hover, setHover] = useState<number | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [figureRef, width] = useChartWidth<HTMLElement>();

  const buckets = useMemo(() => viewBuckets(videos), [videos]);
  const typical = useMemo(() => median(videos.map((video) => video.views)), [videos]);

  if (buckets.length === 0 || typical === null) {
    return (
      <figure ref={figureRef}>
        <p className="rounded-field bg-surface px-4 py-6 text-center text-sm text-muted">
          Cần ít nhất 3 video có số liệu để vẽ phân bố lượt xem.
        </p>
      </figure>
    );
  }

  const threshold = typical * VIRAL;
  const viralCount = videos.filter((video) => typical > 0 && video.views >= threshold).length;
  const maxCount = Math.max(...buckets.map((bucket) => bucket.videos.length));
  const { upper, ticks } = niceScale(0, maxCount, { zeroBased: true, targetTicks: 4 });
  const innerWidth = width - PAD.left - PAD.right;
  const innerHeight = HEIGHT - PAD.top - PAD.bottom;
  const slot = innerWidth / buckets.length;
  const y = (value: number) => PAD.top + (1 - value / upper) * innerHeight;
  const labelEvery = slot < 46 ? 2 : 1;

  const position = (value: number): number | null => {
    const index = buckets.findIndex((bucket) => value >= bucket.from && value < bucket.to);
    if (index === -1) return null;
    const bucket = buckets[index];
    return PAD.left + (index + (value - bucket.from) / (bucket.to - bucket.from)) * slot;
  };

  const medianX = position(typical);
  const viralX = typical > 0 ? position(threshold) : null;
  const active = hover ?? selected;
  const focus = active === null ? null : buckets[active];
  const label = (index: number) => `${compact(buckets[index].from)}–${compact(buckets[index].to)}`;

  return (
    <figure ref={figureRef} className="flex flex-col gap-3">
      <figcaption className="min-h-[40px] text-sm">
        {focus ? (
          <>
            <span className="font-medium">{label(active ?? 0)} lượt xem</span>
            <span className="text-muted">
              {' '}
              · {focus.videos.length} video ({percent(focus.videos.length / videos.length, 0)})
            </span>
          </>
        ) : (
          <span className="text-[13px] text-muted">Rê chuột vào cột để xem số video, bấm để liệt kê video trong khoảng đó.</span>
        )}
      </figcaption>
      <svg
        role="img"
        aria-label="Phân bố số video theo khoảng lượt xem"
        viewBox={`0 0 ${width} ${HEIGHT}`}
        width={width}
        height={HEIGHT}
        className="block max-w-full"
        onMouseLeave={() => setHover(null)}
      >
        {ticks.map((tick) => (
          <g key={tick}>
            <line x1={PAD.left} x2={width - PAD.right} y1={y(tick)} y2={y(tick)} stroke="var(--border)" />
            <text x={PAD.left - 8} y={y(tick) + 4} textAnchor="end" fontSize="11" fill="var(--muted)">
              {tick}
            </text>
          </g>
        ))}
        {buckets.map((bucket, index) => {
          const count = bucket.videos.length;
          const isActive = index === active;
          return (
            <g
              key={bucket.from}
              onMouseEnter={() => setHover(index)}
              onClick={() => setSelected((current) => (current === index ? null : index))}
              style={{ cursor: count > 0 ? 'pointer' : 'default' }}
            >
              <rect x={PAD.left + index * slot} y={PAD.top} width={slot} height={innerHeight} fill="transparent" />
              <rect
                x={PAD.left + index * slot + 3}
                y={y(count)}
                width={Math.max(1, slot - 6)}
                height={PAD.top + innerHeight - y(count)}
                rx="3"
                fill={typical > 0 && bucket.from >= threshold ? 'var(--red)' : 'var(--blue)'}
                opacity={isActive ? 1 : 0.65}
                style={{ transition: 'opacity 120ms' }}
              />
              {isActive && count > 0 ? (
                <text x={PAD.left + index * slot + slot / 2} y={y(count) - 5} textAnchor="middle" fontSize="12" fontWeight="600" fill="var(--fg)">
                  {count}
                </text>
              ) : null}
              {index % labelEvery === 0 ? (
                <text x={PAD.left + index * slot} y={HEIGHT - 28} fontSize="11" fill="var(--muted)" textAnchor="start">
                  {compact(bucket.from)}
                </text>
              ) : null}
            </g>
          );
        })}
        <text
          transform={`translate(13 ${PAD.top + innerHeight / 2}) rotate(-90)`}
          textAnchor="middle"
          fontSize="11"
          fill="var(--muted)"
        >
          Số video
        </text>
        <text x={PAD.left + innerWidth / 2} y={HEIGHT - 6} textAnchor="middle" fontSize="11" fill="var(--muted)">
          Khoảng lượt xem của video
        </text>
        {medianX !== null ? (
          <line x1={medianX} x2={medianX} y1={PAD.top} y2={PAD.top + innerHeight} stroke="var(--muted)" strokeWidth="2.5" strokeDasharray="7 4" />
        ) : null}
        {viralX !== null ? (
          <line x1={viralX} x2={viralX} y1={PAD.top} y2={PAD.top + innerHeight} stroke="var(--red)" strokeWidth="2.5" strokeDasharray="7 4" />
        ) : null}
      </svg>
      <p className="flex flex-wrap items-center gap-x-5 gap-y-1 text-[13px] text-muted">
        <span className="inline-flex items-center gap-1.5">
          <SeriesSwatch color="var(--muted)" dash="7 4" />
          Trung vị {compact(typical)}
        </span>
        <span className="inline-flex items-center gap-1.5">
          <SeriesSwatch color="var(--red)" dash="7 4" />
          Ngưỡng viral {compact(threshold)} ({viralCount} video)
        </span>
      </p>
      {selected !== null && buckets[selected].videos.length > 0 ? (
        <ul className="flex flex-col divide-y divide-border rounded-field border border-border text-sm">
          {[...buckets[selected].videos]
            .sort((a, b) => b.views - a.views)
            .slice(0, 5)
            .map((video) => (
              <li key={video.id} className="flex items-center justify-between gap-3 px-3 py-2">
                {video.url ? (
                  <a href={video.url} target="_blank" rel="noreferrer" className="min-w-0 truncate hover:underline">
                    {video.caption || video.platform_video_id}
                  </a>
                ) : (
                  <span className="min-w-0 truncate">{video.caption || video.platform_video_id}</span>
                )}
                <span className="shrink-0 text-[13px] text-muted">
                  {shortDate(new Date(video.posted_at))} · {compact(video.views)}
                </span>
              </li>
            ))}
        </ul>
      ) : null}
    </figure>
  );
}
