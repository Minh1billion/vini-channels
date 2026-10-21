export type JobStatus = 'running' | 'success' | 'failed';

export interface FetchJobRecord {
  id: string;
  kind: 'register' | 'sync';
  label: string;
  status: JobStatus;
  stage: string;
  done: number;
  total: number | null;
  message: string;
  channel_id: string | null;
  started_at: string;
  finished_at: string | null;
}
