import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { cn } from '@/shared/lib/cn';

interface Props extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'aria-label'> {
  label: string;
  children: ReactNode;
  bordered?: boolean;
  size?: 'sm' | 'md';
}

export function IconButton({ label, children, bordered, size = 'md', className, type = 'button', ...rest }: Props) {
  return (
    <button
      type={type}
      aria-label={label}
      title={label}
      className={cn(
        'inline-flex shrink-0 items-center justify-center rounded-field text-up transition-[color,background-color,transform] duration-150 hover:bg-surface active:scale-90 disabled:active:scale-100',
        size === 'md' ? 'h-9 w-9' : 'h-7 w-7',
        bordered && 'border border-border bg-card',
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}
