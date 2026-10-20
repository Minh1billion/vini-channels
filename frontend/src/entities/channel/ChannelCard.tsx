import { Archive, ArchiveRestore, Clapperboard, Eye, Flame, Globe, Handshake, KeyRound, Pencil } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { ChannelOverview } from '@/entities/analytics/types';
import { cn } from '@/shared/lib/cn';
import { compact, full, percent } from '@/shared/lib/format';
import { Button, IconButton } from '@/shared/ui';
import { ChannelAvatar } from './ChannelAvatar';
import { GrowthPill } from './GrowthPill';
import { PeriodCaption, StatCell } from './StatCell';
import { StatusBadge } from './StatusBadge';
import { toneFor } from './tone';
import type { ChannelRecord } from './types';

interface Props {
  channel: ChannelRecord;
  partnerName?: string;
  stat?: ChannelOverview;
  periodText: string;
  canWrite: boolean;
  onEdit: (channel: ChannelRecord) => void;
  onToggleArchive: (channel: ChannelRecord) => void;
}

export function ChannelCard({ channel, partnerName, stat, periodText, canWrite, onEdit, onToggleArchive }: Props) {
  const tone = toneFor(channel.id);
  const archived = Boolean(channel.archived_at);
  const name = channel.display_name || `@${channel.handle}`;
  const Mode = channel.connection_mode === 'authorized' ? KeyRound : Globe;

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
          onClick={() => onToggleArchive(channel)}
        >
          {archived ? <ArchiveRestore className="h-4 w-4" aria-hidden /> : <Archive className="h-4 w-4" aria-hidden />}
        </IconButton>
      ) : null}

      <div className="flex items-center gap-3 pr-9">
        <ChannelAvatar name={channel.display_name || channel.handle} tone={tone} src={channel.avatar_url} size={40} />
        <div className="min-w-0 flex-1">
          <Link
            to={`/channels/${channel.id}`}
            className="block truncate text-[15px] font-bold leading-tight after:absolute after:inset-0 after:content-[''] focus-visible:outline-none"
          >
            {name}
          </Link>
          <span className="flex items-center gap-1 text-xs text-muted">
            <span className="truncate font-mono">@{channel.handle}</span>
            <Mode
              className="h-3 w-3 shrink-0"
              aria-label={channel.connection_mode === 'authorized' ? 'Ủy quyền' : 'Công khai'}
            />
          </span>
        </div>
      </div>

      <div className="flex items-end justify-between gap-2">
        <div>
          <div
            className="text-[34px] font-bold leading-9 tracking-tight tabular-nums"
            title={stat?.followers == null ? undefined : full(stat.followers)}
          >
            {compact(stat?.followers)}
          </div>
          <div className="text-xs text-muted">người theo dõi</div>
        </div>
        <div className="flex flex-col items-end gap-1.5">
          {archived ? (
            <span className="inline-flex h-6 items-center rounded-full border border-border bg-card px-2 text-xs font-medium">
              Đã lưu trữ
            </span>
          ) : (
            <StatusBadge status={channel.status} />
          )}
          {stat ? <GrowthPill growth={stat.follower_growth} ratio={stat.follower_growth_ratio} /> : null}
        </div>
      </div>

      <PeriodCaption text={periodText} />
      <div className="grid grid-cols-3 gap-2">
        <StatCell icon={Eye} label="Lượt xem" value={stat ? compact(stat.views) : '—'} />
        <StatCell icon={Clapperboard} label="Video" value={stat ? full(stat.video_count) : '—'} />
        <StatCell icon={Flame} label="Tương tác" value={percent(stat?.erv)} />
      </div>

      <footer className="relative z-10 flex min-h-9 items-center justify-between gap-2 border-t border-border pt-3">
        <span className="flex min-w-0 items-center gap-1.5 text-xs text-muted">
          <Handshake className="h-3.5 w-3.5 shrink-0" aria-hidden />
          <span className="truncate">{partnerName ?? '—'}</span>
        </span>
        {canWrite && !archived ? (
          <Button variant="secondary" size="sm" className="shrink-0" onClick={() => onEdit(channel)}>
            <Pencil className="h-3.5 w-3.5" aria-hidden />
            Cập nhật
          </Button>
        ) : null}
      </footer>
    </article>
  );
}
