import type { ReactNode } from 'react';

export function Kbd({ children }: { children: ReactNode }) {
  return (
    <kbd className="inline-flex h-5 items-center rounded border border-border bg-surface px-1.5 font-sans text-[11px] font-medium text-muted">
      {children}
    </kbd>
  );
}
