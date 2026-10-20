import { useId, type TextareaHTMLAttributes } from 'react';
import { cn } from '@/shared/lib/cn';

interface Props extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  hint?: string;
}

export function TextAreaField({ label, hint, className, id, rows = 3, ...rest }: Props) {
  const auto = useId();
  const fieldId = id ?? auto;
  const noteId = `${fieldId}-note`;
  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      <label htmlFor={fieldId} className="text-sm font-medium">
        {label}
      </label>
      <textarea
        id={fieldId}
        rows={rows}
        aria-describedby={hint ? noteId : undefined}
        className="w-full rounded-field border border-border bg-card px-3 py-2 text-sm placeholder:text-muted focus:border-fg focus:outline-none disabled:opacity-60"
        {...rest}
      />
      {hint ? (
        <p id={noteId} className="text-[13px] text-muted">
          {hint}
        </p>
      ) : null}
    </div>
  );
}
