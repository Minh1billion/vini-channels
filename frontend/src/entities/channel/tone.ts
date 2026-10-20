import type { AvatarTone } from './types';

const TONES: AvatarTone[] = ['ink', 'red', 'cyan', 'gray'];

function hashString(text: string): number {
  let hash = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

export function toneFor(key: string): AvatarTone {
  return TONES[hashString(key) % TONES.length];
}
