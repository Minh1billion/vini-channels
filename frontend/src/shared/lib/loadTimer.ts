import { useSyncExternalStore } from 'react';

export interface LoadState {
  status: 'idle' | 'loading' | 'done';
  ms: number;
}

const SETTLE_MS = 60;

let state: LoadState = { status: 'idle', ms: 0 };
let pending = 0;
let startedAt = 0;
let active = false;
let timer: ReturnType<typeof setTimeout> | null = null;
const listeners = new Set<() => void>();

function publish(next: LoadState) {
  state = next;
  listeners.forEach((listener) => listener());
}

function settle() {
  if (timer) clearTimeout(timer);
  timer = null;
  if (!active) return;
  const finishedAt = performance.now();
  timer = setTimeout(() => {
    timer = null;
    if (!active || pending > 0) return;
    active = false;
    publish({ status: 'done', ms: Math.round(finishedAt - startedAt) });
  }, SETTLE_MS);
}

export function beginNavigation() {
  if (timer) clearTimeout(timer);
  timer = null;
  active = true;
  startedAt = performance.now();
  publish({ status: 'loading', ms: 0 });
  settle();
}

export function trackLoad() {
  pending += 1;
  if (timer) clearTimeout(timer);
  timer = null;
  let finished = false;
  return () => {
    if (finished) return;
    finished = true;
    pending = Math.max(0, pending - 1);
    if (pending === 0) settle();
  };
}

export function useLoadState() {
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    () => state,
  );
}
