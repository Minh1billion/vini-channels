import type { SyncRunRecord, SyncScheduleRecord, SyncStatus } from '@/entities/sync/types';
import { http } from './http';

export type SyncRunParams = { limit?: number; status?: SyncStatus; channel_id?: string };

export const syncApi = {
  runs: (params: SyncRunParams = {}) => http.get<SyncRunRecord[]>('/sync/runs', params),
  schedules: () => http.get<SyncScheduleRecord[]>('/sync/schedules'),
  syncChannel: (channelId: string) => http.post<SyncRunRecord>(`/channels/${channelId}/sync`),
};
