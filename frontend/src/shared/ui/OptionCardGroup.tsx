import { useId, type ReactNode } from 'react';
import { cn } from '@/shared/lib/cn';

export interface Option<T extends string> {
  value: T;
  label: string;
  description?: ReactNode;
  disabledReason?: string;
}

interface Props<T extends string> {
  label: string;
  value: T | '';
  options: Array<Option<T>>;
  onChange: (value: T) => void;
  hint?: string;
}

export function OptionCardGroup<T extends string>({ label, value, options, onChange, hint }: Props<T>) {
  const name = useId();
  const labelId = `${name}-label`;
  return (
    <div className="flex flex-col gap-1.5">
      <span id={labelId} className="text-sm font-medium">
        {label}
      </span>
      <div role="radiogroup" aria-labelledby={labelId} className="grid grid-cols-1 gap-2 sm:grid-cols-2">
        {options.map((option) => {
          const disabled = Boolean(option.disabledReason);
          return (
            <label key={option.value} className={cn('relative block', disabled ? 'cursor-not-allowed' : 'cursor-pointer')}>
              <input
                type="radio"
                name={name}
                value={option.value}
                checked={value === option.value}
                disabled={disabled}
                onChange={() => onChange(option.value)}
                className="peer sr-only"
              />
              <span
                className={cn(
                  'flex h-full flex-col gap-0.5 rounded-field border border-border bg-card p-3 transition-colors',
                  'peer-checked:border-fg peer-checked:bg-surface peer-focus-visible:ring-2 peer-focus-visible:ring-fg',
                  disabled ? 'opacity-60' : 'hover:bg-surface',
                )}
              >
                <span className="text-sm font-medium">{option.label}</span>
                <span className="text-[13px] text-muted">{option.disabledReason ?? option.description}</span>
              </span>
            </label>
          );
        })}
      </div>
      {hint ? <p className="text-[13px] text-muted">{hint}</p> : null}
    </div>
  );
}
