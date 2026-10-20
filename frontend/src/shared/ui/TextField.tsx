import { useId, type InputHTMLAttributes } from 'react';
import { cn } from '@/shared/lib/cn';

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
}

export function TextField({ label, error, hint, className, id, ...rest }: Props) {
  const auto = useId();
  const fieldId = id ?? auto;
  const noteId = `${fieldId}-note`;
  const note = error ?? hint;
  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      <label htmlFor={fieldId} className="text-sm font-medium">
        {label}
      </label>
      <input
        id={fieldId}
        aria-invalid={error ? true : undefined}
        aria-describedby={note ? noteId : undefined}
        className={cn(
          'h-10 w-full rounded-field border bg-card px-3 text-sm placeholder:text-muted focus:border-fg focus:outline-none disabled:opacity-60',
          error ? 'border-fg' : 'border-border',
        )}
        {...rest}
      />
      {note ? (
        <p id={noteId} className={cn('text-[13px]', error ? 'text-down' : 'text-muted')}>
          {note}
        </p>
      ) : null}
    </div>
  );
}
