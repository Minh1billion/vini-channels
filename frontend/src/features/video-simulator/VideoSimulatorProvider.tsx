import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';
import type { VideoPreview } from '@/entities/video-source/source';

interface SimulatorValue {
  source: VideoPreview | null;
  openSignal: number;
  show: (source: VideoPreview) => void;
  clear: () => void;
}

const SimulatorContext = createContext<SimulatorValue | null>(null);

export function VideoSimulatorProvider({ children }: { children: ReactNode }) {
  const [source, setSource] = useState<VideoPreview | null>(null);
  const [openSignal, setOpenSignal] = useState(0);

  const show = useCallback((next: VideoPreview) => {
    setSource(next);
    setOpenSignal((n) => n + 1);
  }, []);

  const clear = useCallback(() => setSource(null), []);

  const value = useMemo<SimulatorValue>(() => ({ source, openSignal, show, clear }), [source, openSignal, show, clear]);

  return <SimulatorContext.Provider value={value}>{children}</SimulatorContext.Provider>;
}

export function useVideoSimulator() {
  const value = useContext(SimulatorContext);
  if (!value) throw new Error('useVideoSimulator phải nằm trong VideoSimulatorProvider');
  return value;
}
