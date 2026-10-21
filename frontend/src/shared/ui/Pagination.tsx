import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from './Button';

interface Props {
  page: number;
  pageCount: number;
  onChange: (page: number) => void;
  disabled?: boolean;
}

function pageItems(page: number, pageCount: number): Array<number | 'gap-start' | 'gap-end'> {
  if (pageCount <= 7) return Array.from({ length: pageCount }, (_, index) => index + 1);
  const items: Array<number | 'gap-start' | 'gap-end'> = [1];
  const from = Math.max(2, page - 1);
  const to = Math.min(pageCount - 1, page + 1);
  if (from > 2) items.push('gap-start');
  for (let value = from; value <= to; value += 1) items.push(value);
  if (to < pageCount - 1) items.push('gap-end');
  items.push(pageCount);
  return items;
}

export function Pagination({ page, pageCount, onChange, disabled }: Props) {
  if (pageCount <= 1) return null;
  return (
    <nav aria-label="Phân trang" className="flex flex-wrap items-center justify-center gap-1.5">
      <Button
        size="sm"
        aria-label="Trang trước"
        disabled={disabled || page <= 1}
        onClick={() => onChange(page - 1)}
        className="w-8 px-0"
      >
        <ChevronLeft className="h-4 w-4" aria-hidden />
      </Button>
      {pageItems(page, pageCount).map((item) =>
        typeof item === 'number' ? (
          <Button
            key={item}
            size="sm"
            variant={item === page ? 'primary' : 'secondary'}
            aria-label={`Trang ${item}`}
            aria-current={item === page ? 'page' : undefined}
            disabled={disabled}
            onClick={() => onChange(item)}
            className="min-w-8 px-2"
          >
            {item}
          </Button>
        ) : (
          <span key={item} aria-hidden className="px-1 text-sm text-muted">
            …
          </span>
        ),
      )}
      <Button
        size="sm"
        aria-label="Trang sau"
        disabled={disabled || page >= pageCount}
        onClick={() => onChange(page + 1)}
        className="w-8 px-0"
      >
        <ChevronRight className="h-4 w-4" aria-hidden />
      </Button>
    </nav>
  );
}
