import { X } from 'lucide-react';
import { useEffect, useId, useRef, type ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '@/shared/lib/cn';
import { IconButton } from './IconButton';

type Size = 'sm' | 'md' | 'lg';

const sizes: Record<Size, string> = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
};

interface OverlayProps {
  onClose: () => void;
  children: ReactNode;
  labelledBy?: string;
  describedBy?: string;
  role?: 'dialog' | 'alertdialog';
  dismissible?: boolean;
  className?: string;
}

export function Overlay({
  onClose,
  children,
  labelledBy,
  describedBy,
  role = 'dialog',
  dismissible = true,
  className,
}: OverlayProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && dismissible) onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [onClose, dismissible]);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    const panel = panelRef.current;
    if (panel && !panel.contains(document.activeElement)) panel.focus();
    return () => {
      document.body.style.overflow = overflow;
      previous?.focus?.();
    };
  }, []);

  // Portal ra body: wrapper trang có animate-rise (transform) làm overlay `fixed` bị nhốt trong vùng nội dung.
  return createPortal(
    <div
      className="fixed inset-0 z-50 flex animate-fade-in items-start justify-center overflow-y-auto bg-[rgba(1,1,1,0.55)] p-4 backdrop-blur-[3px] sm:items-center"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && dismissible) onClose();
      }}
    >
      <div
        ref={panelRef}
        tabIndex={-1}
        role={role}
        aria-modal="true"
        aria-labelledby={labelledBy}
        aria-describedby={describedBy}
        className={cn(
          'flex max-h-[calc(100vh-2rem)] w-full animate-dialog-in flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-pop outline-none',
          className,
        )}
      >
        {children}
      </div>
    </div>,
    document.body,
  );
}

interface Props {
  title: string;
  onClose: () => void;
  children: ReactNode;
  description?: string;
  footer?: ReactNode;
  size?: Size;
  dismissible?: boolean;
  className?: string;
}

export function Dialog({
  title,
  onClose,
  children,
  description,
  footer,
  size = 'md',
  dismissible = true,
  className,
}: Props) {
  const titleId = useId();
  const descriptionId = useId();

  return (
    <Overlay
      onClose={onClose}
      dismissible={dismissible}
      labelledBy={titleId}
      describedBy={description ? descriptionId : undefined}
      className={cn(sizes[size], className)}
    >
      <header className="flex shrink-0 items-start justify-between gap-3 px-5 pb-3 pt-4">
        <div className="min-w-0">
          <h2 id={titleId} className="text-lg font-bold leading-6">
            {title}
          </h2>
          {description ? (
            <p id={descriptionId} className="mt-0.5 break-words text-[13px] text-muted">
              {description}
            </p>
          ) : null}
        </div>
        <IconButton label="Đóng" onClick={onClose} disabled={!dismissible} className="-mr-2 -mt-1">
          <X className="h-4 w-4" aria-hidden />
        </IconButton>
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto px-5 pb-5 pt-1">{children}</div>
      {footer ? (
        <footer className="flex shrink-0 items-center gap-3 border-t border-border bg-surface px-5 py-3">{footer}</footer>
      ) : null}
    </Overlay>
  );
}
