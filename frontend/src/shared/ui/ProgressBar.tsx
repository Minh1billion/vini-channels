import { cn } from '@/shared/lib/cn';

interface Props {
  value: number;
  label: string;
  className?: string;
}

export function ProgressBar({ value, label, className }: Props) {
  const clamped = Math.min(100, Math.max(0, value));
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(clamped)}
      className={cn('h-1 w-full overflow-hidden rounded-full bg-border', className)}
    >
      <div className="h-full rounded-full bg-blue transition-[width] duration-500 ease-out" style={{ width: `${clamped}%` }} />
    </div>
  );
}
