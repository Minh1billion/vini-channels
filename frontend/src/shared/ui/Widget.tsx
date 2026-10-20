import type { ReactNode } from 'react';
import { cn } from '@/shared/lib/cn';

interface Props {
  title?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}

export function Widget({ title, actions, children, className, bodyClassName }: Props) {
  return (
    <section className={cn('flex min-w-0 flex-col overflow-hidden rounded-card border border-border bg-card', className)}>
      {title ? (
        <header className="flex h-11 shrink-0 items-center justify-between gap-2 border-b border-border bg-card pl-4 pr-2">
          <h2 className="truncate text-base font-bold">{title}</h2>
          {actions ? <div className="flex items-center gap-0.5">{actions}</div> : null}
        </header>
      ) : null}
      <div className={cn('min-h-0 flex-1', bodyClassName)}>{children}</div>
    </section>
  );
}
