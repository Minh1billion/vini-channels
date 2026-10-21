import { Clapperboard, Eye, Heart, MessageCircle, Share2 } from 'lucide-react';
import { useState } from 'react';
import type { VideoRecord } from '@/entities/analytics/types';
import { compact, percent, shortDate } from '@/shared/lib/format';
import { EmptyState, Skeleton } from '@/shared/ui';

function Stat({ icon: Icon, value, label }: { icon: typeof Eye; value: string; label: string }) {
  return (
    <span className="flex min-w-0 items-center gap-1" title={label}>
      <Icon className="h-3.5 w-3.5 shrink-0 text-muted" aria-hidden />
      <span className="sr-only">{label}</span>
      <span className="truncate">{value}</span>
    </span>
  );
}

function VideoCard({ video }: { video: VideoRecord }) {
  const [broken, setBroken] = useState(false);
  const body = (
    <>
      <div className="relative aspect-[9/12] overflow-hidden rounded-field bg-surface">
        {video.thumbnail_url && !broken ? (
          <img
            src={video.thumbnail_url}
            alt=""
            loading="lazy"
            referrerPolicy="no-referrer"
            onError={() => setBroken(true)}
            className="h-full w-full object-cover"
          />
        ) : (
          <span className="flex h-full w-full items-center justify-center text-muted">
            <Clapperboard className="h-8 w-8" aria-hidden />
          </span>
        )}
        {video.duration_sec > 0 ? (
          <span className="absolute bottom-2 right-2 rounded-full bg-ink px-2 py-0.5 text-xs text-paper">
            {Math.floor(video.duration_sec / 60)}:{String(video.duration_sec % 60).padStart(2, '0')}
          </span>
        ) : null}
      </div>
      <p className="line-clamp-2 min-h-[40px] text-sm">{video.caption || 'Không có chú thích'}</p>
      <p className="flex items-center justify-between text-[13px] text-muted">
        <span className="truncate font-mono text-xs">@{video.handle}</span>
        <time dateTime={video.posted_at}>{shortDate(new Date(video.posted_at))}</time>
      </p>
      <p className="grid grid-cols-4 gap-1 text-[13px]">
        <Stat icon={Eye} value={compact(video.views)} label="Lượt xem" />
        <Stat icon={Heart} value={compact(video.likes)} label="Lượt thích" />
        <Stat icon={MessageCircle} value={compact(video.comments)} label="Bình luận" />
        <Stat icon={Share2} value={compact(video.shares)} label="Chia sẻ" />
      </p>
      <p className="text-[13px] text-muted">Tương tác {percent(video.erv)}</p>
    </>
  );
  const className = 'flex flex-col gap-2 rounded-card border border-border bg-card p-3 transition duration-150 hover:-translate-y-0.5 hover:border-blue';
  return video.url ? (
    <a href={video.url} target="_blank" rel="noreferrer" className={`${className} hover:bg-surface`}>
      {body}
    </a>
  ) : (
    <div className={className}>{body}</div>
  );
}

interface Props {
  videos?: VideoRecord[];
  emptyDescription?: string;
}

export function VideoGrid({ videos, emptyDescription = 'Không có video trong khoảng thời gian này.' }: Props) {
  if (!videos) {
    return (
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        {Array.from({ length: 6 }, (_, i) => (
          <Skeleton key={i} className="h-[320px]" />
        ))}
      </div>
    );
  }
  if (videos.length === 0) {
    return <EmptyState icon={Clapperboard} title="Chưa có video" description={emptyDescription} />;
  }
  return (
    <ul className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
      {videos.map((video) => (
        <li key={video.id} className="min-w-0">
          <VideoCard video={video} />
        </li>
      ))}
    </ul>
  );
}
