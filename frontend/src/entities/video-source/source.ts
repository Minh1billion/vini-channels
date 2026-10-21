import type { VideoRecord } from '@/entities/analytics/types';

export interface VideoPreview {
  id: string;
  handle: string;
  caption: string;
  thumbnailUrl: string | null;
  pageUrl: string | null;
  likes: number;
  comments: number;
  shares: number;
  saves: number | null;
}

export function previewFromRecord(video: VideoRecord): VideoPreview {
  return {
    id: video.id,
    handle: video.handle,
    caption: video.caption,
    thumbnailUrl: video.thumbnail_url,
    pageUrl: video.url,
    likes: video.likes,
    comments: video.comments,
    shares: video.shares,
    saves: video.saves,
  };
}
