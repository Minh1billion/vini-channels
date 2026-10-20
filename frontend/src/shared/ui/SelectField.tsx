import { Check, ChevronDown, type LucideIcon } from 'lucide-react';
import {
  Children,
  Fragment,
  isValidElement,
  useEffect,
  useId,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
  type ReactNode,
} from 'react';
import { createPortal } from 'react-dom';
import { cn } from '@/shared/lib/cn';

interface Item {
  value: string;
  label: string;
  disabled: boolean;
}

interface OptionProps {
  value?: string | number;
  disabled?: boolean;
  children?: ReactNode;
}

interface Props {
  label: string;
  children: ReactNode;
  value?: string;
  onChange?: (event: { target: { value: string } }) => void;
  hideLabel?: boolean;
  icon?: LucideIcon;
  disabled?: boolean;
  required?: boolean;
  className?: string;
  id?: string;
}

function textOf(node: ReactNode): string {
  return Children.toArray(node)
    .map((child) => {
      if (typeof child === 'string' || typeof child === 'number') return String(child);
      return isValidElement<{ children?: ReactNode }>(child) ? textOf(child.props.children) : '';
    })
    .join('');
}

function collect(node: ReactNode, items: Item[]) {
  Children.forEach(node, (child) => {
    if (!isValidElement<OptionProps>(child)) return;
    if (child.type === Fragment) collect(child.props.children, items);
    else if (child.type === 'option') {
      const label = textOf(child.props.children);
      items.push({ value: String(child.props.value ?? label), label, disabled: Boolean(child.props.disabled) });
    }
  });
}

const ROW = 36;
const MAX_HEIGHT = 288;

export function SelectField({
  label,
  hideLabel,
  icon: Icon,
  value,
  onChange,
  disabled,
  required,
  className,
  id,
  children,
}: Props) {
  const auto = useId();
  const fieldId = id ?? auto;
  const listId = `${fieldId}-list`;
  const trigger = useRef<HTMLButtonElement>(null);
  const list = useRef<HTMLUListElement>(null);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const [style, setStyle] = useState<CSSProperties>({});

  const items = useMemo(() => {
    const collected: Item[] = [];
    collect(children, collected);
    return collected;
  }, [children]);

  const selectedIndex = Math.max(0, items.findIndex((item) => item.value === value));
  const selected = items[selectedIndex];

  const close = () => setOpen(false);

  const choose = (index: number) => {
    const item = items[index];
    if (!item || item.disabled) return;
    onChange?.({ target: { value: item.value } });
    close();
    trigger.current?.focus();
  };

  const openList = () => {
    if (disabled) return;
    setActive(selectedIndex);
    setOpen(true);
  };

  useLayoutEffect(() => {
    if (!open || !trigger.current) return;
    const rect = trigger.current.getBoundingClientRect();
    const height = Math.min(items.length * ROW + 8, MAX_HEIGHT);
    const below = window.innerHeight - rect.bottom;
    const up = below < height + 12 && rect.top > below;
    setStyle({
      left: rect.left,
      minWidth: rect.width,
      maxWidth: 'calc(100vw - 16px)',
      ...(up ? { bottom: window.innerHeight - rect.top + 4 } : { top: rect.bottom + 4 }),
    });
  }, [open, items.length]);

  useEffect(() => {
    if (!open) return;
    const onPointer = (event: MouseEvent) => {
      const target = event.target as Node;
      if (trigger.current?.contains(target) || list.current?.contains(target)) return;
      close();
    };
    const onScroll = (event: Event) => {
      if (!list.current?.contains(event.target as Node)) close();
    };
    document.addEventListener('mousedown', onPointer);
    window.addEventListener('scroll', onScroll, true);
    window.addEventListener('resize', close);
    return () => {
      document.removeEventListener('mousedown', onPointer);
      window.removeEventListener('scroll', onScroll, true);
      window.removeEventListener('resize', close);
    };
  }, [open]);

  useEffect(() => {
    if (open) list.current?.children[active]?.scrollIntoView({ block: 'nearest' });
  }, [open, active]);

  const move = (step: number) => {
    if (items.length === 0) return;
    let next = active;
    for (let i = 0; i < items.length; i += 1) {
      next = (next + step + items.length) % items.length;
      if (!items[next]?.disabled) break;
    }
    setActive(next);
  };

  const onKeyDown = (event: KeyboardEvent<HTMLButtonElement>) => {
    switch (event.key) {
      case 'ArrowDown':
      case 'ArrowUp':
        event.preventDefault();
        if (open) move(event.key === 'ArrowDown' ? 1 : -1);
        else openList();
        break;
      case 'Home':
      case 'End':
        if (open) {
          event.preventDefault();
          setActive(event.key === 'Home' ? 0 : items.length - 1);
        }
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        if (open) choose(active);
        else openList();
        break;
      case 'Escape':
        if (open) {
          event.preventDefault();
          event.stopPropagation();
          close();
        }
        break;
      case 'Tab':
        close();
        break;
      default:
    }
  };

  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      <label htmlFor={fieldId} className={cn('text-sm font-medium', hideLabel && 'sr-only')}>
        {label}
      </label>
      <div className="relative">
        {Icon ? (
          <Icon
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
            aria-hidden
          />
        ) : null}
        <button
          ref={trigger}
          id={fieldId}
          type="button"
          role="combobox"
          aria-haspopup="listbox"
          aria-expanded={open}
          aria-controls={open ? listId : undefined}
          aria-activedescendant={open ? `${listId}-${active}` : undefined}
          aria-required={required || undefined}
          disabled={disabled}
          onClick={() => (open ? close() : openList())}
          onKeyDown={onKeyDown}
          className={cn(
            'h-10 w-full rounded-field border bg-card pr-9 text-left text-sm transition-colors hover:bg-surface focus:outline-none focus-visible:border-fg disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:bg-card',
            open ? 'border-fg' : 'border-border',
            Icon ? 'pl-9' : 'pl-3',
          )}
        >
          <span className="block truncate">{selected?.label ?? ''}</span>
        </button>
        <ChevronDown
          className={cn(
            'pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted transition-transform',
            open && 'rotate-180',
          )}
          aria-hidden
        />
      </div>
      {open
        ? createPortal(
            <ul
              ref={list}
              id={listId}
              role="listbox"
              aria-label={label}
              style={style}
              className="fixed z-[60] max-h-72 overflow-y-auto rounded-card border border-border bg-card p-1 shadow-pop"
            >
              {items.map((item, index) => (
                <li
                  key={item.value}
                  id={`${listId}-${index}`}
                  role="option"
                  aria-selected={index === selectedIndex}
                  aria-disabled={item.disabled || undefined}
                  onMouseEnter={() => !item.disabled && setActive(index)}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => choose(index)}
                  className={cn(
                    'flex h-9 cursor-pointer items-center gap-2 rounded-field px-2.5 text-sm',
                    index === active && 'bg-surface',
                    index === selectedIndex && 'font-medium',
                    item.disabled && 'cursor-not-allowed opacity-50',
                  )}
                >
                  <span className="flex-1 truncate">{item.label}</span>
                  {index === selectedIndex ? <Check className="h-4 w-4 shrink-0 text-up" aria-hidden /> : null}
                </li>
              ))}
            </ul>,
            document.body,
          )
        : null}
    </div>
  );
}
