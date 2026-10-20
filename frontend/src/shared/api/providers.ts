import type { ChannelRecord } from '@/entities/channel/types';
import type { ProviderRecord } from '@/entities/provider/types';
import { http } from './http';

export type ProviderUpdateInput = {
  enabled?: boolean;
  priority?: number;
  monthly_quota?: number | null;
  credentials?: Record<string, string>;
};

export type ChannelTokenInput = {
  access_token: string;
  expires_at: string;
  refresh_token?: string | null;
};

export const providersApi = {
  list: () => http.get<ProviderRecord[]>('/providers'),
  update: (key: string, body: ProviderUpdateInput) => http.put<ProviderRecord>(`/providers/${key}`, body),
  setChannelToken: (channelId: string, body: ChannelTokenInput) =>
    http.put<ChannelRecord>(`/channels/${channelId}/credential`, body),
};
