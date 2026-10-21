import { useState } from 'react';
import { cn } from '@/shared/lib/cn';
import { compact, full, percent } from '@/shared/lib/format';

interface Props {
  likes: number;
  comments: number;
  shares: number;
  saves: number | null;
  views: number;
}

interface Part {
  key: string;
  label: string;
  value: number;
  color: string;
}

export function EngagementMix({ likes, comments, shares, saves, views }: Props) {
  const [active, setActive] = useState<string | null>(null);

  const parts: Part[] = [
    { key: 'likes', label: 'Thích', value: likes, color: 'var(--blue)' },
    { key: 'comments', label: 'Bình luận', value: comments, color: 'var(--fg)' },
    { key: 'shares', label: 'Chia sẻ', value: shares, color: 'var(--red)' },
    ...(saves !== null ? [{ key: 'saves', label: 'Lưu', value: saves, color: 'var(--gray)' }] : []),
  ];
  const total = parts.reduce((sum, part) => sum + part.value, 0);

  if (total === 0) {
    return (
      <p className="rounded-field bg-surface px-4 py-6 text-center text-sm text-muted">
        Chưa có lượt tương tác nào trong kỳ này.
      </p>
    );
  }

  const focus = parts.find((part) => part.key === active) ?? null;

  return (
    <div className="flex flex-col gap-4">
      <p className="min-h-[40px] text-sm">
        {focus ? (
          <>
            <span className="font-medium">{focus.label}</span>
            <span className="text-muted">
              {' '}
              · {full(focus.value)} ({percent(focus.value / total)} tổng tương tác)
              {views > 0 ? ` · ${((focus.value / views) * 1000).toFixed(1).replace('.', ',')} trên 1.000 lượt xem` : ''}
            </span>
          </>
        ) : (
          <>
            <span className="font-medium">{compact(total)} tương tác</span>
            <span className="text-muted"> · rê chuột vào từng phần để xem chi tiết</span>
          </>
        )}
      </p>
      <div
        role="img"
        aria-label="Cơ cấu tương tác theo loại"
        className="flex h-8 w-full overflow-hidden rounded-field bg-surface"
        onMouseLeave={() => setActive(null)}
      >
        {parts
          .filter((part) => part.value > 0)
          .map((part) => (
            <span
              key={part.key}
              onMouseEnter={() => setActive(part.key)}
              className={cn('h-full cursor-pointer transition-opacity', active !== null && active !== part.key && 'opacity-35')}
              style={{ width: `${(part.value / total) * 100}%`, backgroundColor: part.color }}
            />
          ))}
      </div>
      <ul className="grid grid-cols-2 gap-3">
        {parts.map((part) => (
          <li
            key={part.key}
            onMouseEnter={() => setActive(part.key)}
            onMouseLeave={() => setActive(null)}
            className={cn(
              'flex cursor-default flex-col gap-0.5 rounded-field border border-border p-3 transition duration-150',
              active === part.key && 'border-blue bg-surface',
            )}
          >
            <span className="flex items-center gap-2 text-[13px] text-muted">
              <span aria-hidden className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: part.color }} />
              {part.label}
            </span>
            <span className="text-lg font-medium">{compact(part.value)}</span>
            <span className="text-[12px] text-muted">
              {percent(part.value / total)} · {views > 0 ? ((part.value / views) * 1000).toFixed(1).replace('.', ',') : '—'} / 1.000 lượt xem
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
