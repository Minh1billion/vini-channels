import {
  CalendarClock,
  CalendarDays,
  CalendarRange,
  Clock,
  Infinity as InfinityIcon,
  SlidersHorizontal,
  type LucideIcon,
} from 'lucide-react';
import { useState } from 'react';
import { lastDays, localDay, type Period } from '@/shared/lib/period';
import { Tabs, TextField } from '@/shared/ui';

type PresetId = 'today' | '7' | '30' | '90' | 'all' | 'custom';

const PRESETS: Array<{ id: PresetId; label: string; icon: LucideIcon }> = [
  { id: 'today', label: 'Hôm nay', icon: Clock },
  { id: '7', label: '7 ngày', icon: CalendarDays },
  { id: '30', label: '30 ngày', icon: CalendarRange },
  { id: '90', label: '90 ngày', icon: CalendarClock },
  { id: 'all', label: 'Toàn thời gian', icon: InfinityIcon },
  { id: 'custom', label: 'Tùy chỉnh', icon: SlidersHorizontal },
];

function presetOf(period: Period): PresetId {
  if (period.kind === 'all') return 'all';
  if (period.kind === 'custom') return 'custom';
  return period.days === 1 ? 'today' : (String(period.days) as PresetId);
}

interface Props {
  value: Period;
  onChange: (period: Period) => void;
  label?: string;
}

export function PeriodPicker({ value, onChange, label = 'Khoảng thời gian' }: Props) {
  const [from, setFrom] = useState(value.kind === 'custom' ? value.from : localDay(-6));
  const [to, setTo] = useState(value.kind === 'custom' ? value.to : localDay());
  const today = localDay();
  const invalid = Boolean(from && to && from > to);

  const choose = (id: PresetId) => {
    if (id === 'custom') onChange({ kind: 'custom', from, to });
    else if (id === 'all') onChange({ kind: 'all' });
    else onChange(lastDays(id === 'today' ? 1 : Number(id)));
  };

  const edit = (nextFrom: string, nextTo: string) => {
    setFrom(nextFrom);
    setTo(nextTo);
    if (nextFrom && nextTo && nextFrom <= nextTo) onChange({ kind: 'custom', from: nextFrom, to: nextTo });
  };

  return (
    <div>
      <div className="overflow-x-auto">
        <Tabs tabs={PRESETS} value={presetOf(value)} onChange={choose} label={label} />
      </div>
      {value.kind === 'custom' ? (
        <div className="flex flex-wrap items-start gap-3 pt-3">
          <TextField
            label="Từ ngày"
            type="date"
            value={from}
            max={to || today}
            onChange={(event) => edit(event.target.value, to)}
            className="w-44"
          />
          <TextField
            label="Đến ngày"
            type="date"
            value={to}
            min={from}
            max={today}
            onChange={(event) => edit(from, event.target.value)}
            error={invalid ? 'Ngày kết thúc phải sau ngày bắt đầu' : undefined}
            className="w-44"
          />
        </div>
      ) : null}
    </div>
  );
}
