import type { ChannelRecord } from '@/entities/channel/types';
import type { Partner } from '@/entities/partner/types';

export interface SearchVideo {
  id: string;
  channel_id: string;
  handle: string;
  caption: string;
  thumbnail_url: string | null;
  posted_at: string;
}

export interface SearchResults {
  partners: Partner[];
  channels: ChannelRecord[];
  videos: SearchVideo[];
}
