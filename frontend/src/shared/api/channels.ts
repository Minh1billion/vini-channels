import type { ChannelRecord } from '@/entities/channel/types';
import { http } from './http';
import type { ChannelTokenInput } from './providers';

export type ChannelListParams = { q?: string; partner_id?: string; include_archived?: boolean };

export type ChannelCreateInput = {
  partner_id: string;
  handle: string;
  provider: string;
  display_name: string;
  sync_cron: string | null;
  timezone: string;
  token?: ChannelTokenInput;
  history_since?: string | null;
};

export type ChannelUpdateInput = { display_name?: string; is_active?: boolean };

export const channelsApi = {
  get: (id: string) => http.get<ChannelRecord>(`/channels/${id}`),
  list: (params: ChannelListParams = {}) => http.get<ChannelRecord[]>('/channels', params),
  create: (body: ChannelCreateInput) => http.post<ChannelRecord>('/channels', body),
  update: (id: string, body: ChannelUpdateInput) => http.patch<ChannelRecord>(`/channels/${id}`, body),
  setSchedule: (id: string, cron: string | null, timezone: string) =>
    http.put<ChannelRecord>(`/channels/${id}/schedule`, { cron, timezone }),
  archive: (id: string) => http.delete<ChannelRecord>(`/channels/${id}`),
  restore: (id: string) => http.post<ChannelRecord>(`/channels/${id}/restore`),
};
