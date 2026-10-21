import { Bookmark, ExternalLink, Heart, MessageCircle, Share2, Smartphone, Trash2, type LucideIcon } from 'lucide-react';
import type { VideoPreview } from '@/entities/video-source/source';
import { useVideoSimulator } from '@/features/video-simulator/VideoSimulatorProvider';
import { compact } from '@/shared/lib/format';
import { IconButton } from '@/shared/ui';

const SCREEN_HEIGHT = 'min(52vh, 480px)';

function RailItem({ icon: Icon, value }: { icon: LucideIcon; value: number | null }) {
  return (
    <span className="flex flex-col items-center gap-0.5 text-[11px] font-semibold leading-3">
      <Icon className="h-6 w-6 fill-paper text-paper drop-shadow" aria-hidden />
      {value === null ? '—' : compact(value)}
    </span>
  );
}

function Feed({ source }: { source: VideoPreview }) {
  return (
    <>
      {source.thumbnailUrl ? (
        <img
          src={source.thumbnailUrl}
          alt=""
          draggable={false}
          referrerPolicy="no-referrer"
          className="absolute inset-0 h-full w-full object-cover"
        />
      ) : null}
      <div className="absolute inset-x-0 bottom-0 h-3/5 bg-gradient-to-t from-[rgba(1,1,1,0.85)] to-transparent" aria-hidden />
      <div className="absolute inset-x-0 bottom-0 flex items-end gap-2 p-3 text-paper">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-bold">@{source.handle}</p>
          <p className="mt-1 line-clamp-2 text-xs leading-4">{source.caption || 'Không có chú thích'}</p>
        </div>
        <div className="flex shrink-0 flex-col items-center gap-3">
          <RailItem icon={Heart} value={source.likes} />
          <RailItem icon={MessageCircle} value={source.comments} />
          <RailItem icon={Bookmark} value={source.saves} />
          <RailItem icon={Share2} value={source.shares} />
        </div>
      </div>
    </>
  );
}

function Screen({ source }: { source: VideoPreview | null }) {
  const frame =
    'relative mx-auto block aspect-[9/16] overflow-hidden rounded-[28px] border-[6px] border-ink bg-ink transition-transform duration-200 ease-out';
  const style = { height: SCREEN_HEIGHT };

  if (!source) {
    return (
      <div className={frame} style={style}>
        <div className="flex h-full w-full flex-col items-center justify-center gap-3 bg-gradient-to-b from-ink to-[#1f2232] px-6 text-center text-paper">
          <Smartphone className="h-9 w-9 opacity-60" aria-hidden />
          <p className="text-sm font-semibold">Chưa chọn video</p>
          <p className="text-xs leading-4 opacity-60">Bấm vào thẻ video để xem trước giao diện trên TikTok</p>
        </div>
      </div>
    );
  }

  if (source.pageUrl) {
    return (
      <a
        href={source.pageUrl}
        target="_blank"
        rel="noreferrer"
        aria-label="Mở video trên TikTok"
        title="Mở video trên TikTok"
        className={`${frame} hover:scale-[1.015]`}
        style={style}
      >
        <Feed source={source} />
      </a>
    );
  }

  return (
    <div className={frame} style={style}>
      <Feed source={source} />
    </div>
  );
}

export function SimulatorPane() {
  const { source, clear } = useVideoSimulator();

  return (
    <div className="flex h-full flex-col justify-center gap-3 p-3">
      <Screen source={source} />

      {source ? (
        <div className="flex items-center gap-2">
          <p className="min-w-0 flex-1 text-xs text-muted">
            Chỉ là bản xem trước giao diện TikTok, không phát video. Bấm vào màn hình để mở link TikTok.
          </p>
          {source.pageUrl ? (
            <a
              href={source.pageUrl}
              target="_blank"
              rel="noreferrer"
              aria-label="Mở trên TikTok"
              title="Mở trên TikTok"
              className="inline-flex h-7 w-7 items-center justify-center rounded-field transition-colors hover:bg-surface"
            >
              <ExternalLink className="h-4 w-4" aria-hidden />
            </a>
          ) : null}
          <IconButton label="Gỡ xem trước" size="sm" onClick={clear}>
            <Trash2 className="h-4 w-4" aria-hidden />
          </IconButton>
        </div>
      ) : (
        <p className="text-center text-xs text-muted">Chỉ xem trước giao diện, không phát video.</p>
      )}
    </div>
  );
}
