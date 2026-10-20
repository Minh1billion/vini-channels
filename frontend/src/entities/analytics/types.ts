export interface TrendPoint {
  day: string;
  followers: number;
  total_likes: number;
  video_count: number;
}

export interface ChannelOverview {
  channel_id: string;
  followers: number | null;
  follower_growth: number;
  follower_growth_ratio: number | null;
  views: number;
  video_count: number;
  average_views: number | null;
  erv: number | null;
}

export interface Overview {
  period_start: string;
  period_end: string;
  days: number;
  channel_count: number;
  followers: number;
  follower_growth: number;
  views: number;
  views_change: number | null;
  video_count: number;
  video_count_change: number | null;
  erv: number | null;
  erv_change: number | null;
  channels: ChannelOverview[];
}

export interface MetricsValues {
  video_count: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  total_shares: number;
  average_views: number | null;
  median_views: number | null;
  erv: number | null;
  follower_growth: number;
  follower_growth_ratio: number | null;
  posts_per_week: number | null;
}

export interface ChannelMetrics {
  channel_id: string;
  period_start: string;
  period_end: string;
  days: number;
  current: MetricsValues;
  previous: MetricsValues;
  erv_change: number | null;
  average_views_change: number | null;
}

export interface DailyViews {
  day: string;
  views: number;
}

export interface VideoGrowth {
  video_id: string;
  platform_video_id: string;
  caption: string;
  posted_at: string;
  views: number;
  views_24h: number | null;
  views_72h: number | null;
  curve: Array<{ age_days: number; views: number }>;
}

export interface CompareResult {
  range: string;
  channels: ChannelMetrics[];
}

export type VideoSort = 'posted' | 'views' | 'likes' | 'comments' | 'shares' | 'erv';

export interface VideoRecord {
  id: string;
  channel_id: string;
  handle: string;
  platform_video_id: string;
  url: string | null;
  caption: string;
  thumbnail_url: string | null;
  duration_sec: number;
  posted_at: string;
  captured_at: string;
  views: number;
  likes: number;
  comments: number;
  shares: number;
  saves: number | null;
  erv: number | null;
}
