import { compact, full, percent } from '@/shared/lib/format';
import type { Overview } from './types';

export interface Kpi {
  label: string;
  value: string;
  delta?: string | null;
  deltaValue?: number | null;
  hint?: string;
  note?: string;
}

export const changeRatio = (current: number, previous: number): number | null =>
  previous === 0 ? null : (current - previous) / previous;

export const signedPercent = (ratio: number | null | undefined): string | null => {
  if (ratio === null || ratio === undefined || !Number.isFinite(ratio)) return null;
  return `${ratio > 0 ? '+' : ''}${percent(ratio)}`;
};

export const signedCount = (value: number): string => `${value > 0 ? '+' : ''}${full(value)}`;

export function overviewKpis(overview: Overview): Kpi[] {
  const empty = overview.channel_count === 0;
  const note = 'Chưa có dữ liệu';
  return [
    {
      label: 'Người theo dõi',
      value: empty ? '—' : compact(overview.followers),
      delta: empty ? null : signedCount(overview.follower_growth),
      deltaValue: overview.follower_growth,
      hint: `trong ${overview.days} ngày`,
      note: empty ? note : undefined,
    },
    {
      label: 'Lượt xem',
      value: empty ? '—' : compact(overview.views),
      delta: empty ? null : signedPercent(overview.views_change),
      deltaValue: overview.views_change,
      hint: 'so với kỳ trước',
      note: empty ? note : undefined,
    },
    {
      label: 'Tỉ lệ tương tác',
      value: percent(overview.erv),
      delta: empty ? null : signedPercent(overview.erv_change),
      deltaValue: overview.erv_change,
      hint: 'so với kỳ trước',
      note: empty ? note : undefined,
    },
    {
      label: 'Video đã đăng',
      value: empty ? '—' : full(overview.video_count),
      delta: empty ? null : signedPercent(overview.video_count_change),
      deltaValue: overview.video_count_change,
      hint: 'so với kỳ trước',
      note: empty ? note : undefined,
    },
  ];
}
