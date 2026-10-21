import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import type { FetchJobRecord } from '@/entities/job/types';
import { jobsApi, type ChannelCreateInput } from '@/shared/api';

const POLL_MS = 1500;
const FINISHED_EVENT = 'fetch-jobs:finished';

interface FetchJobsValue {
  jobs: FetchJobRecord[];
  startRegister: (input: ChannelCreateInput) => Promise<void>;
  startSync: (channelId: string) => Promise<void>;
  dismiss: (id: string) => void;
  dismissFinished: () => void;
  isSyncing: (channelId: string) => boolean;
}

const FetchJobsContext = createContext<FetchJobsValue | null>(null);

function notifyFinished(job: FetchJobRecord) {
  if (!('Notification' in window) || Notification.permission !== 'granted') return;
  const title =
    job.status === 'success' ? `Đã lấy xong dữ liệu ${job.label}` : `Lấy dữ liệu ${job.label} thất bại`;
  new Notification(title, { body: job.message, tag: job.id });
}

function askPermission() {
  if ('Notification' in window && Notification.permission === 'default') {
    void Notification.requestPermission();
  }
}

export function FetchJobsProvider({ children }: { children: ReactNode }) {
  const [jobs, setJobs] = useState<FetchJobRecord[]>([]);
  const [dismissed, setDismissed] = useState<ReadonlySet<string>>(new Set());
  const known = useRef(new Map<string, FetchJobRecord['status']>());

  const apply = useCallback((incoming: FetchJobRecord[], announce: boolean) => {
    for (const job of incoming) {
      const before = known.current.get(job.id);
      if (announce && before === 'running' && job.status !== 'running') {
        notifyFinished(job);
        window.dispatchEvent(new Event(FINISHED_EVENT));
      }
      known.current.set(job.id, job.status);
    }
    setJobs(incoming);
  }, []);

  const refresh = useCallback(
    async (announce: boolean) => {
      try {
        apply(await jobsApi.list(), announce);
      } catch {
        return;
      }
    },
    [apply],
  );

  const hasRunning = jobs.some((job) => job.status === 'running');

  useEffect(() => {
    void refresh(false);
  }, [refresh]);

  useEffect(() => {
    if (!hasRunning) return;
    const timer = window.setInterval(() => void refresh(true), POLL_MS);
    return () => window.clearInterval(timer);
  }, [hasRunning, refresh]);

  const start = useCallback(
    async (request: () => Promise<FetchJobRecord>) => {
      askPermission();
      const job = await request();
      known.current.set(job.id, job.status);
      setJobs((current) => [job, ...current.filter((item) => item.id !== job.id)]);
    },
    [],
  );

  const value = useMemo<FetchJobsValue>(
    () => ({
      jobs: jobs.filter((job) => !dismissed.has(job.id)),
      startRegister: (input) => start(() => jobsApi.registerChannel(input)),
      startSync: (channelId) => start(() => jobsApi.syncChannel(channelId)),
      dismiss: (id) => setDismissed((current) => new Set(current).add(id)),
      dismissFinished: () =>
        setDismissed(
          (current) =>
            new Set([...current, ...jobs.filter((job) => job.status !== 'running').map((job) => job.id)]),
        ),
      isSyncing: (channelId) =>
        jobs.some((job) => job.status === 'running' && job.kind === 'sync' && job.channel_id === channelId),
    }),
    [jobs, dismissed, start],
  );

  return <FetchJobsContext.Provider value={value}>{children}</FetchJobsContext.Provider>;
}

export function useFetchJobs() {
  const value = useContext(FetchJobsContext);
  if (!value) throw new Error('useFetchJobs phải nằm trong FetchJobsProvider');
  return value;
}

export function useOnJobFinished(callback: () => void) {
  const latest = useRef(callback);
  latest.current = callback;
  useEffect(() => {
    const handler = () => latest.current();
    window.addEventListener(FINISHED_EVENT, handler);
    return () => window.removeEventListener(FINISHED_EVENT, handler);
  }, []);
}
