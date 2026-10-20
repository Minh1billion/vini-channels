import type { Overview } from '@/entities/analytics/types';
import type { Channel } from '@/entities/channel/types';
import type { SyncHealth, SyncRunRecord, SyncScheduleRecord } from '@/entities/sync/types';

export interface AttentionItem {
  id: string;
  kind: 'revoked' | 'expiring' | 'failing';
  handle: string;
  tone: Channel['tone'];
  avatarUrl: string | null;
  message: string;
}

export interface DashboardData {
  overview: Overview;
  counts: { partners: number; channels: number };
  connection: { expiring: number; revoked: number };
  recent: Channel[];
  attention: AttentionItem[];
  sync?: { health: SyncHealth; runs: SyncRunRecord[]; schedules: SyncScheduleRecord[] };
}
