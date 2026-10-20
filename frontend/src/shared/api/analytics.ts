import type {
  ChannelMetrics,
  CompareResult,
  DailyViews,
  VideoGrowth,
  Overview,
  TrendPoint,
  VideoRecord,
  VideoSort,
} from '@/entities/analytics/types';
import { periodQuery, type Period } from '@/shared/lib/period';
import { http } from './http';

export type VideoParams = {
  channel_id?: string;
  period: Period;
  q?: string;
  sort?: VideoSort;
  order?: 'asc' | 'desc';
  limit?: number;
};

export const analyticsApi = {
  overview: (period: Period) => http.get<Overview>('/analytics/overview', periodQuery(period)),
  compare: (channelIds: string[], period: Period) =>
    http.get<CompareResult>('/analytics/compare', { channel_ids: channelIds.join(','), ...periodQuery(period) }),
  metrics: (channelId: string, period: Period) =>
    http.get<ChannelMetrics>(`/channels/${channelId}/metrics`, periodQuery(period)),
  dailyViews: (channelId: string, period: Period) =>
    http.get<DailyViews[]>(`/channels/${channelId}/daily-views`, periodQuery(period)),
  videoGrowth: (channelId: string, period: Period) =>
    http.get<VideoGrowth[]>(`/channels/${channelId}/video-growth`, periodQuery(period)),
  trend: (channelId: string, period: Period) =>
    http.get<TrendPoint[]>(`/channels/${channelId}/trend`, periodQuery(period)),
  videos: ({ period, ...params }: VideoParams) =>
    http.get<VideoRecord[]>('/videos', { ...params, ...periodQuery(period) }),
};
