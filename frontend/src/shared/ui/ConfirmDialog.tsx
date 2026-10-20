import { HelpCircle, type LucideIcon } from 'lucide-react';
import { createContext, useCallback, useContext, useId, useRef, useState, type ReactNode } from 'react';
import { Button } from './Button';
import { Overlay } from './Dialog';

export interface ConfirmOptions {
  title: string;
  message?: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  icon?: LucideIcon;
}

interface ConfirmDialogProps extends ConfirmOptions {
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  title,
  message,
  confirmLabel = 'Xác nhận',
  cancelLabel = 'Hủy',
  icon: Icon = HelpCircle,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  const titleId = useId();
  const messageId = useId();

  return (
    <Overlay
      role="alertdialog"
      onClose={onCancel}
      labelledBy={titleId}
      describedBy={message ? messageId : undefined}
      className="max-w-sm"
    >
      <div className="flex flex-col items-center gap-3 px-6 pb-5 pt-7 text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-surface">
          <Icon className="h-6 w-6" strokeWidth={1.75} aria-hidden />
        </span>
        <div className="flex flex-col gap-1.5">
          <h2 id={titleId} className="text-lg font-bold leading-6">
            {title}
          </h2>
          {message ? (
            <p id={messageId} className="break-words text-sm text-muted">
              {message}
            </p>
          ) : null}
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 px-5 pb-5">
        <Button onClick={onCancel} className="!rounded-full">
          {cancelLabel}
        </Button>
        <Button variant="primary" onClick={onConfirm} autoFocus>
          {confirmLabel}
        </Button>
      </div>
    </Overlay>
  );
}

type ConfirmFn = (options: ConfirmOptions) => Promise<boolean>;

const ConfirmContext = createContext<ConfirmFn | null>(null);

export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [options, setOptions] = useState<ConfirmOptions | null>(null);
  const resolver = useRef<((value: boolean) => void) | null>(null);

  const confirm = useCallback<ConfirmFn>((next) => {
    resolver.current?.(false);
    return new Promise<boolean>((resolve) => {
      resolver.current = resolve;
      setOptions(next);
    });
  }, []);

  const settle = (value: boolean) => {
    resolver.current?.(value);
    resolver.current = null;
    setOptions(null);
  };

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {options ? <ConfirmDialog {...options} onConfirm={() => settle(true)} onCancel={() => settle(false)} /> : null}
    </ConfirmContext.Provider>
  );
}

export function useConfirm(): ConfirmFn {
  const confirm = useContext(ConfirmContext);
  if (!confirm) throw new Error('useConfirm must be used within ConfirmProvider');
  return confirm;
}
