import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

interface Props {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action }: Props) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-6 py-10 text-center">
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-surface">
        <Icon className="h-5 w-5 text-muted" aria-hidden />
      </span>
      <p className="font-bold">{title}</p>
      {description ? <p className="max-w-sm text-muted">{description}</p> : null}
      {action}
    </div>
  );
}
