import type { ReactNode } from 'react';
import { cn } from '@/shared/lib/cn';

interface Props {
  children: ReactNode;
  active?: boolean;
  tone?: 'default' | 'red';
  onClick?: () => void;
  className?: string;
}

export function Chip({ children, active, onClick, className, tone = 'default' }: Props) {
  const classes = cn(
    'inline-flex h-7 items-center gap-1 rounded-full border px-3 text-[13px] font-medium transition-colors',
    tone === 'red'
      ? active
        ? 'border-red bg-red text-[var(--on-red)]'
        : 'border-red bg-card text-red'
      : active
        ? 'border-fg bg-fg text-bg'
        : 'border-border bg-card text-fg',
    onClick && !active && 'hover:bg-surface',
    className,
  );
  if (onClick) {
    return (
      <button type="button" aria-pressed={active} onClick={onClick} className={classes}>
        {children}
      </button>
    );
  }
  return <span className={classes}>{children}</span>;
}
