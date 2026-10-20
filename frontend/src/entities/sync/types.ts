import type { ChannelStatus, ConnectionMode } from '@/entities/channel/types';

export type SyncStatus = 'success' | 'partial' | 'failed' | 'running';

export interface SyncHealth {
  month: Date;
  ok: number;
  total: number;
  runs: Array<'ok' | 'failed'>;
}

export interface SyncRunRecord {
  id: string;
  channel_id: string;
  handle: string;
  trigger: 'scheduled' | 'manual';
  status: SyncStatus;
  source: string | null;
  items_fetched: number;
  started_at: string;
  finished_at: string | null;
  duration_sec: number | null;
  error_code: string | null;
  error_message: string | null;
}

export interface SyncScheduleRecord {
  channel_id: string;
  handle: string;
  display_name: string;
  connection_mode: ConnectionMode;
  status: ChannelStatus;
  is_active: boolean;
  cron: string;
  is_default_cron: boolean;
  timezone: string;
  next_run_at: string | null;
}
