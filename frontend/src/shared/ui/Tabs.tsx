import type { LucideIcon } from 'lucide-react';
import { cn } from '@/shared/lib/cn';

interface Tab<T extends string> {
  id: T;
  label: string;
  icon?: LucideIcon;
}

interface Props<T extends string> {
  tabs: Array<Tab<T>>;
  value: T;
  onChange: (value: T) => void;
  label: string;
}

export function Tabs<T extends string>({ tabs, value, onChange, label }: Props<T>) {
  return (
    <div role="tablist" aria-label={label} className="flex gap-5 border-b border-border">
      {tabs.map((tab) => {
        const active = tab.id === value;
        const Icon = tab.icon;
        return (
          <button
            key={tab.id}
            role="tab"
            type="button"
            id={`tab-${tab.id}`}
            aria-selected={active}
            aria-controls={`panel-${tab.id}`}
            onClick={() => onChange(tab.id)}
            className={cn(
              '-mb-px inline-flex h-10 shrink-0 items-center gap-1.5 whitespace-nowrap border-b-2 text-sm transition-colors',
              active ? 'border-blue font-medium text-fg' : 'border-transparent text-muted hover:text-fg',
            )}
          >
            {Icon ? <Icon className="h-4 w-4" aria-hidden /> : null}
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
