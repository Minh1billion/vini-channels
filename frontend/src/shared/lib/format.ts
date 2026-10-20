const DASH = '—';

const UNITS: Array<[number, string]> = [
  [1e9, 'B'],
  [1e6, 'M'],
  [1e3, 'K'],
];

const decimal = (value: number) => value.toFixed(1).replace(/\.0$/, '').replace('.', ',');

export function compact(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return DASH;
  const abs = Math.abs(value);
  for (const [size, suffix] of UNITS) {
    if (abs >= size) return `${decimal(value / size)}${suffix}`;
  }
  return String(Math.round(value));
}

const fullFormatter = new Intl.NumberFormat('vi-VN');

export function full(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return DASH;
  return fullFormatter.format(value);
}

export function percent(ratio: number | null | undefined, digits = 1): string {
  if (ratio === null || ratio === undefined || !Number.isFinite(ratio)) return DASH;
  return `${(ratio * 100).toFixed(digits).replace('.', ',')}%`;
}

export function relativeTime(date: Date, now: Date = new Date()): string {
  const seconds = Math.max(0, Math.round((now.getTime() - date.getTime()) / 1000));
  if (seconds < 60) return 'Vừa xong';
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} phút trước`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.round(hours / 24);
  return `${days} ngày trước`;
}

export function untilTime(date: Date, now: Date = new Date()): string {
  const minutes = Math.max(0, Math.round((date.getTime() - now.getTime()) / 60000));
  if (minutes < 1) return 'Sắp chạy';
  if (minutes < 60) return `Sau ${minutes} phút`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `Sau ${hours} giờ`;
  return `Sau ${Math.round(hours / 24)} ngày`;
}

export function duration(seconds: number | null): string {
  if (seconds === null) return DASH;
  if (seconds < 60) return `${seconds} giây`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return s === 0 ? `${m} phút` : `${m} phút ${s} giây`;
}

const dateTimeFormatter = new Intl.DateTimeFormat('vi-VN', {
  day: '2-digit',
  month: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
});

export const dateTime = (date: Date) => dateTimeFormatter.format(date);

const dateTimeYearFormatter = new Intl.DateTimeFormat('vi-VN', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit',
  hour12: false,
});

export const dateTimeYear = (date: Date) => dateTimeYearFormatter.format(date);

export const shortDate = (date: Date) =>
  `${String(date.getDate()).padStart(2, '0')}/${String(date.getMonth() + 1).padStart(2, '0')}`;

export const monthLabel = (date: Date) => `Tháng ${date.getMonth() + 1}/${date.getFullYear()}`;

export const initials = (text: string) => {
  const clean = text.replace(/^@/, '').trim();
  const parts = clean.split(/[\s._-]+/).filter(Boolean);
  if (parts.length === 0) return '?';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
};
