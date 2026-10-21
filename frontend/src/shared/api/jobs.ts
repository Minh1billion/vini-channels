import type { FetchJobRecord } from '@/entities/job/types';
import type { ChannelCreateInput } from './channels';
import { http } from './http';

export const jobsApi = {
  list: () => http.get<FetchJobRecord[]>('/jobs'),
  registerChannel: (body: ChannelCreateInput) => http.post<FetchJobRecord>('/jobs/channels', body),
  syncChannel: (channelId: string) => http.post<FetchJobRecord>(`/jobs/channels/${channelId}/sync`),
};
