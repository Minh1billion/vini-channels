import { useId, type InputHTMLAttributes } from 'react';
import { cn } from '@/shared/lib/cn';

interface Props extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string;
}

export function CheckboxField({ label, className, id, ...rest }: Props) {
  const auto = useId();
  const fieldId = id ?? auto;
  return (
    <label htmlFor={fieldId} className={cn('inline-flex cursor-pointer items-center gap-2 text-sm', className)}>
      <input id={fieldId} type="checkbox" className="h-4 w-4 accent-[var(--blue)]" {...rest} />
      {label}
    </label>
  );
}
