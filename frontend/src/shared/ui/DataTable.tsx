import type { ReactNode } from 'react';
import { cn } from '@/shared/lib/cn';

export interface Column<T> {
  key: string;
  header: ReactNode;
  cell: (row: T) => ReactNode;
  align?: 'left' | 'right';
  className?: string;
}

interface Props<T> {
  columns: Array<Column<T>>;
  rows: T[];
  rowKey: (row: T) => string;
  caption: string;
  id?: string;
  labelledBy?: string;
}

export function DataTable<T>({ columns, rows, rowKey, caption, id, labelledBy }: Props<T>) {
  return (
    <div id={id} role={labelledBy ? 'tabpanel' : undefined} aria-labelledby={labelledBy} className="overflow-x-auto">
      <table className="w-full min-w-[640px] border-collapse text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="bg-surface">
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={cn(
                  'h-10 px-4 text-xs font-medium text-muted',
                  column.align === 'right' ? 'text-right' : 'text-left',
                  column.className,
                )}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)} className="h-11 border-t border-border transition-colors hover:bg-surface">
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={cn('px-4', column.align === 'right' ? 'text-right' : 'text-left', column.className)}
                >
                  {column.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
