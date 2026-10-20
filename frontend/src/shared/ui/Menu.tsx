import type { LucideIcon } from 'lucide-react';
import { Check } from 'lucide-react';
import { useEffect, useRef, useState, type ReactNode } from 'react';
import { cn } from '@/shared/lib/cn';

interface MenuProps {
  trigger: (state: { open: boolean; toggle: () => void }) => ReactNode;
  children: (close: () => void) => ReactNode;
  align?: 'start' | 'end';
  className?: string;
  direction?: 'down' | 'up';
}

export function Menu({ trigger, children, align = 'end', direction = 'down', className }: MenuProps) {
  const [open, setOpen] = useState(false);
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: MouseEvent) => {
      if (root.current && !root.current.contains(event.target as Node)) setOpen(false);
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onPointer);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onPointer);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  return (
    <div ref={root} className="relative">
      {trigger({ open, toggle: () => setOpen((value) => !value) })}
      {open ? (
        <div
          role="menu"
          className={cn(
            'absolute z-30 min-w-[220px] rounded-card border border-border bg-card p-1 shadow-pop',
            direction === 'down' ? 'top-full mt-2 origin-top animate-pop-in' : 'bottom-full mb-2 origin-bottom animate-pop-in-up',
            align === 'end' ? 'right-0' : 'left-0',
            className,
          )}
        >
          {children(() => setOpen(false))}
        </div>
      ) : null}
    </div>
  );
}

interface ItemProps {
  icon?: LucideIcon;
  children: ReactNode;
  onSelect?: () => void;
  checked?: boolean;
  role?: 'menuitem' | 'menuitemradio' | 'menuitemcheckbox';
  disabled?: boolean;
}

export function MenuItem({ icon: Icon, children, onSelect, checked, role = 'menuitem', disabled }: ItemProps) {
  return (
    <button
      type="button"
      role={role}
      aria-checked={role === 'menuitem' ? undefined : Boolean(checked)}
      disabled={disabled}
      onClick={onSelect}
      className="flex h-9 w-full items-center gap-2 rounded-field px-2.5 text-left text-sm transition-colors hover:bg-surface disabled:opacity-50"
    >
      {Icon ? <Icon className="h-4 w-4 shrink-0 text-muted" aria-hidden /> : null}
      <span className="flex-1">{children}</span>
      {checked ? <Check className="h-4 w-4" aria-hidden /> : null}
    </button>
  );
}

export function MenuSeparator() {
  return <div role="separator" className="my-1 h-px bg-border" />;
}
