import { LayoutGrid, Rows3 } from 'lucide-react';
import { cn } from '@/shared/lib/cn';
import type { ViewMode } from '@/shared/lib/useViewMode';

interface Props {
  value: ViewMode;
  onChange: (value: ViewMode) => void;
  className?: string;
}

const options = [
  { id: 'cards', label: 'Dạng thẻ', icon: LayoutGrid },
  { id: 'table', label: 'Dạng bảng', icon: Rows3 },
] as const;

export function ViewToggle({ value, onChange, className }: Props) {
  return (
    <div
      role="radiogroup"
      aria-label="Kiểu hiển thị"
      className={cn('inline-flex h-10 items-center gap-0.5 rounded-full border border-border bg-card p-1', className)}
    >
      {options.map(({ id, label, icon: Icon }) => {
        const active = value === id;
        return (
          <button
            key={id}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={label}
            title={label}
            onClick={() => onChange(id)}
            className={cn(
              'inline-flex h-8 w-9 items-center justify-center rounded-full transition-colors',
              active ? 'bg-blue text-on-blue' : 'text-muted hover:text-fg',
            )}
          >
            <Icon className="h-4 w-4" aria-hidden />
          </button>
        );
      })}
    </div>
  );
}
