import type { VideoRecord } from './types';

export const WEEKDAYS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];
export const WEEKDAY_NAMES = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật'];

export const hourRange = (hour: number) => `${hour}h–${(hour + 1) % 24}h`;

export function median(values: number[]): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 1 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

export interface Slot {
  weekday: number;
  hour: number;
  count: number;
  views: number;
}

export const slotAverage = (slot: { count: number; views: number }) => (slot.count === 0 ? 0 : slot.views / slot.count);

export function postingSlots(videos: VideoRecord[]): Slot[][] {
  const grid = Array.from({ length: 7 }, (_, weekday) =>
    Array.from({ length: 24 }, (_, hour): Slot => ({ weekday, hour, count: 0, views: 0 })),
  );
  for (const video of videos) {
    const date = new Date(video.posted_at);
    const slot = grid[(date.getDay() + 6) % 7][date.getHours()];
    slot.count += 1;
    slot.views += video.views;
  }
  return grid;
}

export interface Peak {
  index: number;
  count: number;
  average: number;
}

function peak(groups: Array<{ count: number; views: number }>): Peak | null {
  const filled = groups
    .map((group, index) => ({ index, count: group.count, average: slotAverage(group) }))
    .filter((group) => group.count > 0);
  if (filled.length === 0) return null;
  const solid = filled.filter((group) => group.count >= 2);
  return (solid.length > 0 ? solid : filled).reduce((best, group) => (group.average > best.average ? group : best));
}

export interface Facts {
  saves: number | null;
  averageDuration: number | null;
  topShare: number | null;
  bestWeekday: Peak | null;
  bestHour: Peak | null;
}

const addUp = (slots: Slot[]) =>
  slots.reduce((sum, slot) => ({ count: sum.count + slot.count, views: sum.views + slot.views }), { count: 0, views: 0 });

export function channelFacts(videos: VideoRecord[]): Facts {
  const grid = postingSlots(videos);
  const weekdays = grid.map(addUp);
  const hours = Array.from({ length: 24 }, (_, hour) => addUp(grid.map((row) => row[hour])));
  const withSaves = videos.filter((video) => video.saves !== null);
  const withDuration = videos.filter((video) => video.duration_sec > 0);
  const total = videos.reduce((sum, video) => sum + video.views, 0);
  const top = [...videos]
    .sort((a, b) => b.views - a.views)
    .slice(0, 3)
    .reduce((sum, video) => sum + video.views, 0);
  return {
    saves: withSaves.length > 0 ? withSaves.reduce((sum, video) => sum + (video.saves ?? 0), 0) : null,
    averageDuration:
      withDuration.length > 0 ? withDuration.reduce((sum, video) => sum + video.duration_sec, 0) / withDuration.length : null,
    topShare: videos.length > 3 && total > 0 ? top / total : null,
    bestWeekday: peak(weekdays),
    bestHour: peak(hours),
  };
}

export interface Bucket {
  from: number;
  to: number;
  videos: VideoRecord[];
}

function edgesFor(max: number, decades: boolean) {
  const steps = decades ? [1] : [1, 2, 5];
  const edges = [0];
  for (let power = 0; ; power += 1) {
    for (const step of steps) {
      const edge = step * 10 ** power;
      edges.push(edge);
      if (edge > max) return edges;
    }
  }
}

export function viewBuckets(videos: VideoRecord[]): Bucket[] {
  if (videos.length < 3) return [];
  const values = videos.map((video) => video.views);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const build = (decades: boolean): Bucket[] => {
    const edges = edgesFor(max, decades);
    let start = 0;
    while (start + 1 < edges.length && edges[start + 1] <= min) start += 1;
    const slice = edges.slice(start);
    return slice.slice(0, -1).map((from, index) => ({ from, to: slice[index + 1], videos: [] }));
  };
  let buckets = build(false);
  if (buckets.length > 12) buckets = build(true);
  for (const video of videos) {
    buckets.find((bucket) => video.views >= bucket.from && video.views < bucket.to)?.videos.push(video);
  }
  return buckets;
}
