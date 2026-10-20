import type { ReactNode } from 'react';

interface Props {
  title: string;
  description?: string;
  children: ReactNode;
}

export function FormSection({ title, description, children }: Props) {
  return (
    <section className="flex flex-col gap-3 rounded-field border border-border p-3">
      <div>
        <h3 className="text-sm font-bold">{title}</h3>
        {description ? <p className="text-[13px] text-muted">{description}</p> : null}
      </div>
      {children}
    </section>
  );
}
