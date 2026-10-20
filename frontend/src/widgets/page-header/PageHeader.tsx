import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

interface Props {
  title: string;
  description?: string;
  icon?: LucideIcon;
  actions?: ReactNode;
}

export function PageHeader({ title, description, icon: Icon, actions }: Props) {
  return (
    <>
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="flex min-w-0 items-center gap-3">
        {Icon ? (
          <span
            aria-hidden
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-card border border-border bg-surface"
          >
            <Icon className="h-5 w-5" strokeWidth={1.75} />
          </span>
        ) : null}
        <div className="min-w-0">
          <h1 className="text-page font-bold tracking-tight">{title}</h1>
          {description ? <p className="mt-1 text-sm text-muted">{description}</p> : null}
        </div>
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
    <div aria-hidden className="relative mb-6 mt-5 h-px bg-border">
      <span className="absolute -top-[0.5px] left-0 h-0.5 w-12 rounded-full bg-red" />
    </div>
    </>
  );
}
