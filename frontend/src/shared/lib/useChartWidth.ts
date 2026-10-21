import { useEffect, useRef, useState } from 'react';

export function useChartWidth<T extends HTMLElement>(initial = 640, minimum = 280) {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(initial);

  useEffect(() => {
    const element = ref.current;
    if (!element) return undefined;
    const update = () => setWidth(Math.max(minimum, Math.round(element.clientWidth)));
    update();
    const observer = new ResizeObserver(update);
    observer.observe(element);
    return () => observer.disconnect();
  }, [minimum]);

  return [ref, width] as const;
}
