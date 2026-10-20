export type Period =
  | { kind: 'days'; days: number }
  | { kind: 'all' }
  | { kind: 'custom'; from: string; to: string };

export const lastDays = (days: number): Period => ({ kind: 'days', days });

const pad = (value: number) => String(value).padStart(2, '0');

export function localDay(offsetDays = 0) {
  const date = new Date();
  date.setDate(date.getDate() + offsetDays);
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function periodQuery(period: Period): Record<string, string | number> {
  const tz_offset = -new Date().getTimezoneOffset();
  if (period.kind === 'all') return { range: 'all', tz_offset };
  if (period.kind === 'custom') return { date_from: period.from, date_to: period.to, tz_offset };
  return { range: `${period.days}d`, tz_offset };
}

export function periodKey(period: Period) {
  if (period.kind === 'all') return 'all';
  if (period.kind === 'custom') return `${period.from}..${period.to}`;
  return `${period.days}d`;
}

const display = (day: string) => day.split('-').reverse().join('/');

export function periodLabel(period: Period) {
  if (period.kind === 'all') return 'toàn thời gian';
  if (period.kind === 'custom') return `${display(period.from)} - ${display(period.to)}`;
  return period.days === 1 ? 'hôm nay' : `${period.days} ngày qua`;
}
