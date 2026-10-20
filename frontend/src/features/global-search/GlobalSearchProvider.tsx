import { createContext, useCallback, useContext, useEffect, useMemo, useRef, type ReactNode } from 'react';

type Opener = () => boolean;

interface Value {
  open: () => void;
  register: (opener: Opener) => () => void;
}

const GlobalSearchContext = createContext<Value | null>(null);

export function GlobalSearchProvider({ children }: { children: ReactNode }) {
  const openers = useRef<Set<Opener>>(new Set());

  const register = useCallback((opener: Opener) => {
    openers.current.add(opener);
    return () => {
      openers.current.delete(opener);
    };
  }, []);

  const open = useCallback(() => {
    for (const opener of openers.current) {
      if (opener()) return;
    }
  }, []);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        open();
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open]);

  const value = useMemo(() => ({ open, register }), [open, register]);

  return <GlobalSearchContext.Provider value={value}>{children}</GlobalSearchContext.Provider>;
}

export function useSearchRegistry(): Value {
  const value = useContext(GlobalSearchContext);
  if (!value) throw new Error('useSearchRegistry must be used inside GlobalSearchProvider');
  return value;
}
