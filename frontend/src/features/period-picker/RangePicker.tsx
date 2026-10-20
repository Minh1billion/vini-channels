import { ArrowRight, CalendarRange, ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '@/shared/lib/cn';
import { lastDays, localDay, type Period } from '@/shared/lib/period';
import { Button } from '@/shared/ui';

type PresetId = 'today' | '7' | '30' | '90' | 'all' | 'custom';
type Step = 'start' | 'end' | null;
type Range = { from: string; to: string };

interface Draft {
  preset: PresetId;
  from: string | null;
  to: string | null;
}

const PRESETS: Array<{ id: PresetId; label: string }> = [
  { id: 'today', label: 'Hôm nay' },
  { id: '7', label: '7 ngày qua' },
  { id: '30', label: '30 ngày qua' },
  { id: '90', label: '90 ngày qua' },
  { id: 'all', label: 'Toàn thời gian' },
  { id: 'custom', label: 'Tùy chỉnh' },
];

const WEEKDAYS = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'];
const POPOVER_WIDTH = 660;
const POPOVER_HEIGHT = 400;

const pad = (value: number) => String(value).padStart(2, '0');
const iso = (date: Date) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
const parse = (day: string) => {
  const [y, m, d] = day.split('-').map(Number);
  return new Date(y, m - 1, d);
};
const short = (day: string) => `${pad(parse(day).getDate())}/${pad(parse(day).getMonth() + 1)}`;
const long = (day: string) => `${short(day)}/${parse(day).getFullYear()}`;
const ordered = (a: string, b: string): Range => (a <= b ? { from: a, to: b } : { from: b, to: a });

function presetOf(period: Period): PresetId {
  if (period.kind === 'all') return 'all';
  if (period.kind === 'custom') return 'custom';
  if (period.days === 1) return 'today';
  return period.days === 7 || period.days === 30 || period.days === 90 ? (String(period.days) as PresetId) : 'custom';
}

function rangeOf(period: Period): Range | null {
  if (period.kind === 'all') return null;
  if (period.kind === 'custom') return { from: period.from, to: period.to };
  return { from: localDay(-(period.days - 1)), to: localDay() };
}

function presetPeriod(id: PresetId): Period | null {
  if (id === 'all') return { kind: 'all' };
  if (id === 'custom') return null;
  return lastDays(id === 'today' ? 1 : Number(id));
}

function draftOf(period: Period): Draft {
  const range = rangeOf(period);
  return { preset: presetOf(period), from: range?.from ?? null, to: range?.to ?? null };
}

function periodOf(draft: Draft): Period | null {
  if (draft.preset !== 'custom') return presetPeriod(draft.preset);
  return draft.from && draft.to ? { kind: 'custom', from: draft.from, to: draft.to } : null;
}

function titleOf(period: Period) {
  const id = presetOf(period);
  return PRESETS.find((preset) => preset.id === id)?.label ?? 'Tùy chỉnh';
}

function summaryOf(draft: Draft) {
  if (draft.preset === 'all') return 'Toàn thời gian';
  if (!draft.from || !draft.to) return 'Chưa chọn khoảng ngày';
  const days = Math.round((parse(draft.to).getTime() - parse(draft.from).getTime()) / 86400000) + 1;
  return `${long(draft.from)} - ${long(draft.to)} · ${days} ngày`;
}

function monthShift(year: number, month: number, delta: number) {
  const date = new Date(year, month + delta, 1);
  return { year: date.getFullYear(), month: date.getMonth() };
}

interface MonthProps {
  year: number;
  month: number;
  range: Range | null;
  today: string;
  onPick: (day: string) => void;
  onHover: (day: string | null) => void;
  onPrev?: () => void;
  onNext?: () => void;
  nextDisabled?: boolean;
  className?: string;
}

function Month({ year, month, range, today, onPick, onHover, onPrev, onNext, nextDisabled, className }: MonthProps) {
  const offset = (new Date(year, month, 1).getDay() + 6) % 7;
  const count = new Date(year, month + 1, 0).getDate();
  const cells: Array<string | null> = [
    ...Array.from({ length: offset }, () => null),
    ...Array.from({ length: count }, (_, i) => iso(new Date(year, month, i + 1))),
  ];

  return (
    <div className={cn('min-w-0 flex-1', className)}>
      <div className="mb-2 flex h-8 items-center justify-between">
        {onPrev ? (
          <button
            type="button"
            aria-label="Tháng trước"
            onClick={onPrev}
            className="inline-flex h-8 w-8 items-center justify-center rounded-field text-muted hover:bg-surface hover:text-fg"
          >
            <ChevronLeft className="h-4 w-4" aria-hidden />
          </button>
        ) : (
          <span className="h-8 w-8" />
        )}
        <span className="text-[13px] font-bold">
          Tháng {month + 1}/{year}
        </span>
        {onNext ? (
          <button
            type="button"
            aria-label="Tháng sau"
            onClick={onNext}
            disabled={nextDisabled}
            className="inline-flex h-8 w-8 items-center justify-center rounded-field text-muted hover:bg-surface hover:text-fg disabled:opacity-30 disabled:hover:bg-transparent"
          >
            <ChevronRight className="h-4 w-4" aria-hidden />
          </button>
        ) : (
          <span className="h-8 w-8" />
        )}
      </div>
      <div className="grid grid-cols-7 text-center" onMouseLeave={() => onHover(null)}>
        {WEEKDAYS.map((day) => (
          <span key={day} className="pb-1 text-[11px] text-muted">
            {day}
          </span>
        ))}
        {cells.map((day, index) => {
          if (!day) return <span key={`blank-${index}`} />;
          const future = day > today;
          const start = range?.from === day;
          const end = range?.to === day;
          const inside = range ? day > range.from && day < range.to : false;
          const single = range ? range.from === range.to : false;
          return (
            <span
              key={day}
              className={cn(
                'flex h-8 items-center justify-center',
                inside && 'bg-blue-soft',
                start && !single && 'rounded-l-full bg-blue-soft',
                end && !single && 'rounded-r-full bg-blue-soft',
              )}
            >
              <button
                type="button"
                disabled={future}
                aria-label={long(day)}
                aria-pressed={start || end}
                onClick={() => onPick(day)}
                onMouseEnter={() => onHover(day)}
                className={cn(
                  'h-8 w-8 rounded-full text-xs tabular-nums transition-colors',
                  start || end
                    ? 'bg-blue font-bold text-on-blue'
                    : 'hover:bg-surface disabled:text-muted disabled:opacity-40 disabled:hover:bg-transparent',
                  day === today && !start && !end && 'ring-1 ring-fg',
                )}
              >
                {parse(day).getDate()}
              </button>
            </span>
          );
        })}
      </div>
    </div>
  );
}

function DateField({ label, value, active, placeholder }: { label: string; value: string | null; active: boolean; placeholder: string }) {
  return (
    <div
      className={cn(
        'min-w-0 flex-1 rounded-field border px-3 py-1.5 transition-colors',
        active ? 'border-blue ring-1 ring-blue' : 'border-border',
      )}
    >
      <span className={cn('block text-[11px]', active ? 'font-bold text-blue' : 'text-muted')}>{label}</span>
      <span className={cn('block truncate text-sm tabular-nums', value ? 'font-medium' : 'text-muted')}>
        {value ? long(value) : placeholder}
      </span>
    </div>
  );
}

interface Props {
  value: Period;
  onChange: (period: Period) => void;
  align?: 'start' | 'end';
  className?: string;
}

export function RangePicker({ value, onChange, align = 'start', className }: Props) {
  const trigger = useRef<HTMLButtonElement>(null);
  const popover = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<Draft>(() => draftOf(value));
  const [step, setStep] = useState<Step>(null);
  const [hover, setHover] = useState<string | null>(null);
  const [place, setPlace] = useState({ top: 0, left: 0, width: POPOVER_WIDTH });
  const [view, setView] = useState(() => {
    const now = new Date();
    return monthShift(now.getFullYear(), now.getMonth(), -1);
  });
  const today = localDay();

  const reposition = useCallback(() => {
    const el = trigger.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const width = Math.min(POPOVER_WIDTH, window.innerWidth - 32);
    const raw = align === 'end' ? rect.right - width : rect.left;
    const left = Math.max(16, Math.min(raw, window.innerWidth - width - 16));
    const below = rect.bottom + 8;
    const top = below + POPOVER_HEIGHT > window.innerHeight && rect.top - 8 - POPOVER_HEIGHT > 0 ? rect.top - 8 - POPOVER_HEIGHT : below;
    setPlace({ top, left, width });
  }, [align]);

  useLayoutEffect(() => {
    if (open) reposition();
  }, [open, reposition]);

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: MouseEvent) => {
      const target = event.target as Node;
      if (trigger.current?.contains(target) || popover.current?.contains(target)) return;
      setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onPointer);
    document.addEventListener('keydown', onKey);
    window.addEventListener('resize', reposition);
    window.addEventListener('scroll', reposition, true);
    return () => {
      document.removeEventListener('mousedown', onPointer);
      document.removeEventListener('keydown', onKey);
      window.removeEventListener('resize', reposition);
      window.removeEventListener('scroll', reposition, true);
    };
  }, [open, reposition]);

  const showEnd = (to: string | null) => {
    const end = to ? parse(to) : new Date();
    setView(monthShift(end.getFullYear(), end.getMonth(), -1));
  };

  const toggle = () => {
    if (open) {
      setOpen(false);
      return;
    }
    const next = draftOf(value);
    setDraft(next);
    setStep(null);
    setHover(null);
    showEnd(next.to);
    setOpen(true);
  };

  const choosePreset = (id: PresetId) => {
    setHover(null);
    if (id === 'custom') {
      setDraft({ preset: 'custom', from: null, to: null });
      setStep('start');
      return;
    }
    const period = presetPeriod(id);
    const range = period ? rangeOf(period) : null;
    setDraft({ preset: id, from: range?.from ?? null, to: range?.to ?? null });
    setStep(null);
    showEnd(range?.to ?? null);
  };

  const pick = (day: string) => {
    if (step === 'end' && draft.from) {
      const range = ordered(draft.from, day);
      setDraft({ preset: 'custom', from: range.from, to: range.to });
      setStep(null);
      setHover(null);
      return;
    }
    setDraft({ preset: 'custom', from: day, to: null });
    setStep('end');
  };

  const apply = () => {
    const period = periodOf(draft);
    if (!period) return;
    onChange(period);
    setOpen(false);
  };

  const preview: Range | null =
    step === 'end' && draft.from
      ? ordered(draft.from, hover ?? draft.from)
      : draft.from && draft.to
        ? { from: draft.from, to: draft.to }
        : null;

  const next = monthShift(view.year, view.month, 1);
  const now = new Date();
  const nextBlocked = next.year * 12 + next.month >= now.getFullYear() * 12 + now.getMonth();
  const activeRange = rangeOf(value);
  const rangeText = activeRange ? `${short(activeRange.from)} - ${short(activeRange.to)}` : null;
  const canApply = periodOf(draft) !== null && step === null;
  const endPreview = step === 'end' && hover && draft.from ? ordered(draft.from, hover).to : draft.to;
  const startPreview = step === 'end' && hover && draft.from ? ordered(draft.from, hover).from : draft.from;

  const hint =
    step === 'start'
      ? { text: 'Bước 1/2 · Chọn ngày bắt đầu', accent: true }
      : step === 'end'
        ? { text: 'Bước 2/2 · Chọn ngày kết thúc', accent: true }
        : { text: summaryOf(draft), accent: false };

  const goPrev = () => setView((current) => monthShift(current.year, current.month, -1));
  const goNext = () => setView((current) => monthShift(current.year, current.month, 1));

  return (
    <div className={cn('relative', className)}>
      <button
        ref={trigger}
        type="button"
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={toggle}
        className="inline-flex h-10 items-center gap-2 rounded-full border border-border bg-card px-4 text-sm font-medium hover:bg-surface"
      >
        <CalendarRange className="h-4 w-4 text-up" aria-hidden />
        {titleOf(value)}
        {rangeText ? <span className="hidden font-normal text-muted sm:inline">{rangeText}</span> : null}
        <ChevronDown className={cn('h-4 w-4 text-muted transition-transform', open && 'rotate-180')} aria-hidden />
      </button>

      {open
        ? createPortal(
            <div
              ref={popover}
              role="dialog"
              aria-label="Chọn khoảng thời gian"
              style={{ top: place.top, left: place.left, width: place.width }}
              className="fixed z-50 overflow-hidden rounded-card border border-border bg-card text-fg shadow-pop"
            >
              <div className="flex flex-col sm:flex-row">
                <div className="flex shrink-0 gap-1 overflow-x-auto border-b border-border bg-surface p-1.5 sm:w-40 sm:flex-col sm:overflow-visible sm:border-b-0 sm:border-r">
                  {PRESETS.map((preset) => {
                    const active = draft.preset === preset.id;
                    return (
                      <button
                        key={preset.id}
                        type="button"
                        aria-pressed={active}
                        onClick={() => choosePreset(preset.id)}
                        className={cn(
                          'flex h-8 shrink-0 items-center whitespace-nowrap rounded-field px-2.5 text-left text-[13px]',
                          active ? 'bg-card font-bold ring-1 ring-border' : 'hover:bg-card',
                        )}
                      >
                        {preset.label}
                      </button>
                    );
                  })}
                </div>
                <div className="flex min-w-0 flex-1 flex-col gap-3 p-3.5">
                  <div className="flex items-center gap-2">
                    <DateField
                      label="Ngày bắt đầu"
                      value={startPreview}
                      active={step === 'start'}
                      placeholder={step === 'start' ? 'Chọn ngày' : '—'}
                    />
                    <ArrowRight className="h-4 w-4 shrink-0 text-muted" aria-hidden />
                    <DateField
                      label="Ngày kết thúc"
                      value={endPreview}
                      active={step === 'end'}
                      placeholder={step === 'end' ? 'Chọn ngày' : '—'}
                    />
                  </div>
                  <div className="flex gap-5">
                    <Month
                      year={view.year}
                      month={view.month}
                      range={preview}
                      today={today}
                      onPick={pick}
                      onHover={setHover}
                      onPrev={goPrev}
                      onNext={goNext}
                      nextDisabled={nextBlocked}
                      className="sm:hidden"
                    />
                    <Month
                      year={view.year}
                      month={view.month}
                      range={preview}
                      today={today}
                      onPick={pick}
                      onHover={setHover}
                      onPrev={goPrev}
                      className="hidden sm:block"
                    />
                    <Month
                      year={next.year}
                      month={next.month}
                      range={preview}
                      today={today}
                      onPick={pick}
                      onHover={setHover}
                      onNext={goNext}
                      nextDisabled={nextBlocked}
                      className="hidden sm:block"
                    />
                  </div>
                </div>
              </div>
              <div className="flex items-center justify-between gap-3 border-t border-border px-3.5 py-2.5">
                <span
                  role="status"
                  className={cn('min-w-0 truncate text-xs', hint.accent ? 'font-bold text-blue' : 'text-muted')}
                >
                  {hint.text}
                </span>
                <Button variant="accent" size="sm" disabled={!canApply} onClick={apply}>
                  Áp dụng
                </Button>
              </div>
            </div>,
            document.body,
          )
        : null}
    </div>
  );
}
