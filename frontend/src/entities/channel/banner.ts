import type { AvatarTone } from './types';

export const bannerGradient: Record<AvatarTone, string> = {
  ink: 'linear-gradient(135deg, #010101 0%, #1f2232 55%, #5f6168 170%)',
  red: 'linear-gradient(135deg, #5f6168 0%, #2b2f42 60%, #010101 170%)',
  cyan: 'linear-gradient(135deg, #9a9ba1 0%, #3c3f4a 60%, #010101 170%)',
  gray: 'linear-gradient(135deg, #9a9ba1 0%, #5f6168 60%, #010101 170%)',
};
