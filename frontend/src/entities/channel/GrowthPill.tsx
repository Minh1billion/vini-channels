import { Minus, TrendingDown, TrendingUp } from 'lucide-react';
import { signedCount, signedPercent } from '@/entities/analytics/kpis';
import { cn } from '@/shared/lib/cn';

interface Props {
  growth: number;
  ratio?: number | null;
  className?: string;
}

export function GrowthPill({ growth, ratio, className }: Props) {
  const Icon = growth > 0 ? TrendingUp : growth < 0 ? TrendingDown : Minus;
  const percent = signedPercent(ratio);
  return (
    <span
      className={cn(
        'inline-flex h-6 items-center gap-1 rounded-full px-2 text-xs font-bold',
        growth > 0 && 'bg-blue-soft text-blue',
        growth < 0 && 'bg-surface text-fg',
        growth === 0 && 'bg-surface text-muted',
        className,
      )}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden />
      {signedCount(growth)}
      {percent ? <span className="font-medium opacity-80">({percent})</span> : null}
    </span>
  );
}
