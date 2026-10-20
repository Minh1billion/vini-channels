import { Archive, ArchiveRestore, AtSign, Clapperboard, Eye, Pencil } from 'lucide-react';
import { Link } from 'react-router-dom';
import { ChannelAvatar } from '@/entities/channel/ChannelAvatar';
import { GrowthPill } from '@/entities/channel/GrowthPill';
import { PeriodCaption, StatCell } from '@/entities/channel/StatCell';
import { toneFor } from '@/entities/channel/tone';
import type { ChannelRecord } from '@/entities/channel/types';
import { cn } from '@/shared/lib/cn';
import { compact, full } from '@/shared/lib/format';
import { Button, IconButton } from '@/shared/ui';
import type { Partner } from './types';

export interface PartnerStats {
  followers: number;
  growth: number;
  views: number;
  videos: number;
  hasData: boolean;
}

interface Props {
  partner: Partner;
  channels: ChannelRecord[];
  stats: PartnerStats;
  periodText: string;
  canWrite: boolean;
  onEdit: (partner: Partner) => void;
  onToggleArchive: (partner: Partner) => void;
}

const MAX_FACES = 4;

export function PartnerCard({ partner, channels, stats, periodText, canWrite, onEdit, onToggleArchive }: Props) {
  const tone = toneFor(partner.id);
  const archived = Boolean(partner.archived_at);
  const faces = channels.slice(0, MAX_FACES);
  const extra = channels.length - faces.length;

  return (
    <article
      className={cn(
        'relative flex flex-col gap-3.5 rounded-card border border-[color:color-mix(in_srgb,var(--fg)_35%,transparent)] bg-card p-4 transition-all hover:-translate-y-0.5 hover:shadow-pop',
        archived && 'opacity-60',
      )}
    >
      {canWrite ? (
        <IconButton
          label={archived ? 'Khôi phục' : 'Lưu trữ'}
          size="sm"
          className="absolute right-2.5 top-2.5 z-10 !text-muted"
          onClick={() => onToggleArchive(partner)}
        >
          {archived ? <ArchiveRestore className="h-4 w-4" aria-hidden /> : <Archive className="h-4 w-4" aria-hidden />}
        </IconButton>
      ) : null}

      <div className="flex items-center gap-3 pr-9">
        <ChannelAvatar name={partner.name} tone={tone} src={partner.logo_url} size={40} />
        <div className="min-w-0 flex-1">
          <Link
            to={`/channels?partner_id=${partner.id}`}
            className="block truncate text-[15px] font-bold leading-tight after:absolute after:inset-0 after:content-[''] focus-visible:outline-none"
          >
            {partner.name}
          </Link>
          <span className="block truncate text-xs text-muted">{partner.industry ?? 'Chưa phân ngành'}</span>
        </div>
      </div>

      {partner.tags.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {partner.tags.map((tag) => (
            <span key={tag} className="rounded-full bg-cyan-soft px-2.5 py-0.5 text-xs font-medium text-up">
              #{tag}
            </span>
          ))}
        </div>
      ) : null}

      <div className="flex items-end justify-between gap-2">
        <div>
          <div className="text-[34px] font-bold leading-9 tracking-tight tabular-nums">
            {stats.hasData ? compact(stats.followers) : '—'}
          </div>
          <div className="text-xs text-muted">người theo dõi, tất cả kênh</div>
        </div>
        <div className="flex flex-col items-end gap-1.5">
          {archived ? (
            <span className="inline-flex h-6 items-center rounded-full border border-border bg-card px-2 text-xs font-medium">
              Đã lưu trữ
            </span>
          ) : null}
          {stats.hasData ? <GrowthPill growth={stats.growth} /> : null}
        </div>
      </div>

      <PeriodCaption text={periodText} />
      <div className="grid grid-cols-3 gap-2">
        <StatCell icon={AtSign} label="Kênh" value={String(partner.channel_count)} />
        <StatCell icon={Eye} label="Lượt xem" value={stats.hasData ? compact(stats.views) : '—'} />
        <StatCell icon={Clapperboard} label="Video" value={stats.hasData ? full(stats.videos) : '—'} />
      </div>

      <footer className="relative z-10 flex min-h-9 items-center justify-between gap-2 border-t border-border pt-3">
        <span className="flex min-w-0 items-center gap-2 text-xs text-muted">
          {channels.length === 0 ? (
            'Chưa có kênh'
          ) : (
            <>
              <span className="flex shrink-0 items-center">
                {faces.map((channel, index) => (
                  <ChannelAvatar
                    key={channel.id}
                    name={channel.display_name || channel.handle}
                    tone={toneFor(channel.id)}
                    src={channel.avatar_url}
                    size={24}
                    className={cn('ring-2 ring-card', index > 0 && '-ml-1.5')}
                  />
                ))}
                {extra > 0 ? (
                  <span className="-ml-1.5 inline-flex h-6 min-w-6 items-center justify-center rounded-full bg-surface px-1 text-[10px] font-bold text-fg ring-2 ring-card">
                    +{extra}
                  </span>
                ) : null}
              </span>
              <span className="truncate">{channels.length} kênh</span>
            </>
          )}
        </span>
        {canWrite && !archived ? (
          <Button variant="secondary" size="sm" className="shrink-0" onClick={() => onEdit(partner)}>
            <Pencil className="h-3.5 w-3.5" aria-hidden />
            Cập nhật
          </Button>
        ) : null}
      </footer>
    </article>
  );
}
