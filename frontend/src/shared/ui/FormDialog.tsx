import { Loader2 } from 'lucide-react';
import { useId, useState, type FormEvent, type ReactNode } from 'react';
import { errorMessage } from '@/shared/lib/errors';
import { Button } from './Button';
import { Dialog } from './Dialog';

interface Props {
  title: string;
  submitLabel: string;
  onSubmit: () => Promise<void>;
  onClose: () => void;
  children: ReactNode;
  description?: string;
  size?: 'sm' | 'md' | 'lg';
  pendingLabel?: string;
  pendingNote?: string;
  canSubmit?: boolean;
}

export function FormDialog({
  title,
  submitLabel,
  onSubmit,
  onClose,
  children,
  description,
  size,
  pendingLabel = 'Đang lưu...',
  pendingNote,
  canSubmit = true,
}: Props) {
  const formId = useId();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (submitting || !canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit();
    } catch (err) {
      setError(errorMessage(err));
      setSubmitting(false);
    }
  };

  const status = error ? (
    <p role="alert" className="break-words text-sm text-down">
      {error}
    </p>
  ) : submitting && pendingNote ? (
    <p role="status" className="text-[13px] text-muted">
      {pendingNote}
    </p>
  ) : null;

  return (
    <Dialog
      title={title}
      description={description}
      size={size}
      onClose={onClose}
      dismissible={!submitting}
      footer={
        <>
          <div className="min-w-0 flex-1">{status}</div>
          <div className="flex shrink-0 gap-2">
            <Button onClick={onClose} disabled={submitting}>
              Hủy
            </Button>
            <Button type="submit" form={formId} variant="primary" disabled={submitting || !canSubmit}>
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : null}
              {submitting ? pendingLabel : submitLabel}
            </Button>
          </div>
        </>
      }
    >
      <form id={formId} onSubmit={submit}>
        <fieldset disabled={submitting} className="m-0 flex min-w-0 flex-col gap-4 border-0 p-0">
          {children}
        </fieldset>
      </form>
    </Dialog>
  );
}
