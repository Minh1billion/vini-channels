import { Clapperboard, ExternalLink, Eye, Heart, MessageCircle, Play, Share2 } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { VideoRecord } from '@/entities/analytics/types';
import { previewFromRecord } from '@/entities/video-source/source';
import { useVideoSimulator } from '@/features/video-simulator/VideoSimulatorProvider';
import { compact, percent, shortDate } from '@/shared/lib/format';
import { EmptyState, Skeleton } from '@/shared/ui';

function Stat({ icon: Icon, value, label }: { icon: typeof Eye; value: string; label: string }) {
  return (
    <span className="flex shrink-0 items-center gap-1" title={label}>
      <Icon className="h-3.5 w-3.5 shrink-0 text-muted" aria-hidden />
      <span className="sr-only">{label}</span>
      <span>{value}</span>
    </span>
  );
}

function VideoCard({ video }: { video: VideoRecord }) {
  const [broken, setBroken] = useState(false);
  const { show } = useVideoSimulator();
  const preview = previewFromRecord(video);

  return (
    <div
      className="flex flex-col gap-2 rounded-card border border-border bg-card p-3 transition duration-200 ease-out hover:-translate-y-0.5 hover:border-blue"
    >
      <div className="relative aspect-[9/12] overflow-hidden rounded-field bg-surface">
        <button
          type="button"
          onClick={() => show(preview)}
          aria-label={`Xem trước trên TikTok: ${video.caption || 'video không có chú thích'}`}
          className="group block h-full w-full"
        >
          {video.thumbnail_url && !broken ? (
            <img
              src={video.thumbnail_url}
              alt=""
              loading="lazy"
              draggable={false}
              referrerPolicy="no-referrer"
              onError={() => setBroken(true)}
              className="h-full w-full object-cover"
            />
          ) : (
            <span className="flex h-full w-full items-center justify-center text-muted">
              <Clapperboard className="h-8 w-8" aria-hidden />
            </span>
          )}
          <span className="absolute inset-0 flex items-center justify-center bg-transparent opacity-0 transition group-hover:bg-[rgba(1,1,1,0.3)] group-hover:opacity-100 group-focus-visible:opacity-100">
            <Play className="h-9 w-9 fill-paper text-paper" aria-hidden />
          </span>
        </button>
        {video.url ? (
          <a
            href={video.url}
            target="_blank"
            rel="noreferrer"
            draggable={false}
            aria-label="Mở trên TikTok"
            title="Mở trên TikTok"
            className="absolute right-2 top-2 flex h-7 w-7 items-center justify-center rounded-full bg-[rgba(1,1,1,0.72)] text-paper shadow-sm ring-1 ring-[rgba(255,255,255,0.35)] backdrop-blur-sm transition-colors hover:bg-ink"
          >
            <ExternalLink className="h-3.5 w-3.5" aria-hidden />
          </a>
        ) : null}
        {video.duration_sec > 0 ? (
          <span className="pointer-events-none absolute bottom-2 right-2 rounded-full bg-ink px-2 py-0.5 text-xs text-paper">
            {Math.floor(video.duration_sec / 60)}:{String(video.duration_sec % 60).padStart(2, '0')}
          </span>
        ) : null}
      </div>
      <p className="line-clamp-2 min-h-[40px] text-sm">{video.caption || 'Không có chú thích'}</p>
      <p className="flex items-center justify-between text-[13px] text-muted">
        <Link
          to={`/channels/${video.channel_id}`}
          title="Mở trang kênh"
          className="truncate font-mono text-xs transition-colors hover:text-fg hover:underline"
        >
          @{video.handle}
        </Link>
        <time dateTime={video.posted_at}>{shortDate(new Date(video.posted_at))}</time>
      </p>
      <p className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 text-[13px]">
        <Stat icon={Eye} value={compact(video.views)} label="Lượt xem" />
        <Stat icon={Heart} value={compact(video.likes)} label="Lượt thích" />
        <Stat icon={MessageCircle} value={compact(video.comments)} label="Bình luận" />
        <Stat icon={Share2} value={compact(video.shares)} label="Chia sẻ" />
      </p>
      <p className="text-[13px] text-muted">Tương tác {percent(video.erv)}</p>
    </div>
  );
}

interface Props {
  videos?: VideoRecord[];
  emptyDescription?: string;
  single?: boolean;
}

export function VideoGrid({ videos, emptyDescription = 'Không có video trong khoảng thời gian này.', single = false }: Props) {
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
    <ul className={single ? 'grid grid-cols-1' : 'grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6'}>
      {videos.map((video) => (
        <li key={video.id} className="min-w-0">
          <VideoCard video={video} />
        </li>
      ))}
    </ul>
  );
}
