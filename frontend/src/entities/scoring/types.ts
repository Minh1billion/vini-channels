export type ScoreComponent = 'engagement' | 'growth' | 'reach' | 'consistency';

export type ScoreWeights = Record<ScoreComponent, number>;

export const scoreComponents: ReadonlyArray<{ key: ScoreComponent; label: string; hint: string }> = [
  { key: 'engagement', label: 'Tương tác', hint: 'Tỉ lệ tương tác theo lượt xem' },
  { key: 'growth', label: 'Tăng trưởng', hint: 'Tăng trưởng người theo dõi trong kỳ' },
  { key: 'reach', label: 'Độ phủ', hint: 'Lượt xem trung bình so với người theo dõi' },
  { key: 'consistency', label: 'Đều đặn', hint: 'Số video đăng mỗi tuần' },
];

export interface ChannelScore {
  channel_id: string;
  partner_id: string;
  partner_name: string;
  handle: string;
  display_name: string;
  rank: number | null;
  total: number | null;
  components: Record<ScoreComponent, number | null>;
  erv: number | null;
  follower_growth_ratio: number | null;
  reach_ratio: number | null;
  posts_per_week: number | null;
}

export interface PartnerScore {
  partner_id: string;
  name: string;
  rank: number | null;
  total: number | null;
  channel_count: number;
  scored_channel_count: number;
}

export interface Scoreboard {
  period_start: string;
  period_end: string;
  days: number;
  weights: ScoreWeights;
  channels: ChannelScore[];
  partners: PartnerScore[];
}
