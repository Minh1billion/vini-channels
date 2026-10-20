import { useState } from 'react';
import { cn } from '@/shared/lib/cn';
import { sourceLabel } from './labels';

const custom = import.meta.glob<string>('/src/assets/providers/*.{svg,png,webp}', {
  eager: true,
  query: '?url',
  import: 'default',
});

const customByKey: Record<string, string> = Object.fromEntries(
  Object.entries(custom).map(([path, url]) => [path.split('/').pop()!.replace(/\.[^.]+$/, ''), url]),
);

const TIKTOK_PATH =
  'M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z';

const sizes = {
  20: 'h-5 w-5 rounded-md text-[10px]',
  28: 'h-7 w-7 rounded-lg text-xs',
  36: 'h-9 w-9 rounded-lg text-sm',
} as const;

interface LogoProps {
  providerKey: string;
  size?: keyof typeof sizes;
  className?: string;
}

export function ProviderLogo({ providerKey, size = 28, className }: LogoProps) {
  const [failed, setFailed] = useState(false);
  const url = customByKey[providerKey];
  const base = 'inline-flex shrink-0 select-none items-center justify-center overflow-hidden font-bold ring-1 ring-border';

  if (url && !failed) {
    return (
      <span aria-hidden className={cn(base, 'bg-white', sizes[size], className)}>
        <img src={url} alt="" onError={() => setFailed(true)} className="h-full w-full object-cover" />
      </span>
    );
  }

  if (providerKey === 'tiktok') {
    return (
      <span aria-hidden className={cn(base, 'bg-ink text-paper', sizes[size], className)}>
        <svg viewBox="0 0 24 24" fill="currentColor" className="h-[58%] w-[58%]">
          <path d={TIKTOK_PATH} />
        </svg>
      </span>
    );
  }

  return (
    <span aria-hidden className={cn(base, 'bg-surface text-fg', sizes[size], className)}>
      {sourceLabel(providerKey).charAt(0).toUpperCase()}
    </span>
  );
}

export function SourceTag({ source, size = 20 }: { source: string | null; size?: keyof typeof sizes }) {
  if (!source) return <span>—</span>;
  return (
    <span className="inline-flex items-center gap-2">
      <ProviderLogo providerKey={source} size={size} />
      {sourceLabel(source)}
    </span>
  );
}
