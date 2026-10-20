import { CalendarRange, type LucideIcon } from 'lucide-react';

export function StatCell({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-lg bg-surface p-2.5">
      <span className="flex items-center gap-1.5 text-[11px] text-muted">
        <Icon className="h-3.5 w-3.5 shrink-0 text-up" aria-hidden />
        <span className="truncate">{label}</span>
      </span>
      <span className="mt-1 block text-base font-bold tabular-nums">{value}</span>
    </div>
  );
}

export function PeriodCaption({ text }: { text: string }) {
  return (
    <div className="-mb-1.5 flex items-center gap-1.5 text-[11px] text-muted">
      <CalendarRange className="h-3 w-3" aria-hidden />
      Thông số {text}
    </div>
  );
}
