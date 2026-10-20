import { useCallback, useState } from 'react';

export type ViewMode = 'cards' | 'table';

export function useViewMode(key: string): [ViewMode, (mode: ViewMode) => void] {
  const [mode, setMode] = useState<ViewMode>(() => {
    try {
      return localStorage.getItem(key) === 'table' ? 'table' : 'cards';
    } catch {
      return 'cards';
    }
  });

  const update = useCallback(
    (next: ViewMode) => {
      setMode(next);
      try {
        localStorage.setItem(key, next);
      } catch {
        return;
      }
    },
    [key],
  );

  return [mode, update];
}
