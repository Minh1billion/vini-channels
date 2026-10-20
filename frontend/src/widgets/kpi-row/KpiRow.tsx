import { Activity, Clapperboard, Eye, TrendingDown, TrendingUp, Users, type LucideIcon } from 'lucide-react';
import type { Kpi } from '@/entities/analytics/kpis';
import { cn } from '@/shared/lib/cn';
import { Skeleton, Widget } from '@/shared/ui';

const icons: LucideIcon[] = [Users, Eye, Activity, Clapperboard];

function Delta({ kpi }: { kpi: Kpi }) {
  if (!kpi.delta) return kpi.note ? <span className="text-[13px] text-muted">{kpi.note}</span> : null;
  const down = (kpi.deltaValue ?? 0) < 0;
  const Icon = down ? TrendingDown : TrendingUp;
  return (
    <span className="flex items-center gap-1.5 text-[13px] text-muted">
      <span className={cn('inline-flex items-center gap-1 font-medium', down ? 'text-down' : 'text-blue')}>
        <Icon className="h-3.5 w-3.5" aria-hidden />
        {kpi.delta}
      </span>
      {kpi.hint}
    </span>
  );
}

export function KpiRow({ items }: { items?: Kpi[] }) {
  return (
    <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {(items ?? Array.from({ length: 4 }, () => null)).map((kpi, index) => {
        const Icon = icons[index % icons.length];
        return (
          <li key={kpi?.label ?? index} className="animate-rise" style={{ animationDelay: `${index * 60}ms` }}>
            <Widget className="h-full" bodyClassName="flex flex-col gap-1 p-4">
              {kpi ? (
                <>
                  <span className="flex items-center gap-2 text-[13px] text-muted">
                    <span aria-hidden className="flex h-6 w-6 items-center justify-center rounded-full bg-blue text-on-blue">
                      <Icon className="h-3.5 w-3.5" />
                    </span>
                    {kpi.label}
                  </span>
                  <span className="text-kpi font-medium">{kpi.value}</span>
                  <Delta kpi={kpi} />
                </>
              ) : (
                <Skeleton className="h-[88px]" />
              )}
            </Widget>
          </li>
        );
      })}
    </ul>
  );
}
