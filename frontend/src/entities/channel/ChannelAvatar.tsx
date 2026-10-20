import { useEffect, useState } from 'react';
import { cn } from '@/shared/lib/cn';
import { initials } from '@/shared/lib/format';
import type { AvatarTone } from './types';

const tones: Record<AvatarTone, string> = {
  ink: 'bg-ink text-paper ring-1 ring-border',
  red: 'bg-surface text-fg ring-1 ring-border',
  cyan: 'bg-blue-soft text-blue ring-1 ring-border',
  gray: 'bg-gray text-ink',
};

const sizes = {
  24: 'h-6 w-6 text-[10px]',
  32: 'h-8 w-8 text-xs',
  40: 'h-10 w-10 text-sm',
  48: 'h-12 w-12 text-base',
  64: 'h-16 w-16 text-xl',
} as const;

interface Props {
  name: string;
  tone: AvatarTone;
  src?: string | null;
  size?: keyof typeof sizes;
  className?: string;
}

export function ChannelAvatar({ name, tone, src, size = 40, className }: Props) {
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setFailed(false);
  }, [src]);

  const image = src && !failed ? src : null;

  return (
    <span
      aria-hidden
      className={cn(
        'inline-flex shrink-0 select-none items-center justify-center overflow-hidden rounded-full font-bold',
        image ? 'bg-surface ring-1 ring-border' : tones[tone],
        sizes[size],
        className,
      )}
    >
      {image ? (
        <img
          src={image}
          alt=""
          loading="lazy"
          referrerPolicy="no-referrer"
          onError={() => setFailed(true)}
          className="h-full w-full object-cover"
        />
      ) : (
        initials(name)
      )}
    </span>
  );
}
