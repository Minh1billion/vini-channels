import { ArrowRight, AtSign } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { ChannelAvatar } from '@/entities/channel/ChannelAvatar';
import { StatusBadge } from '@/entities/channel/StatusBadge';
import type { Channel } from '@/entities/channel/types';
import { useAuth } from '@/features/auth/AuthProvider';
import { Button, EmptyState, Skeleton, Widget } from '@/shared/ui';

export function RecentChannels({ data }: { data?: Channel[] }) {
  const { can } = useAuth();
  const navigate = useNavigate();
  return (
    <Widget title="Kênh" className="h-full">
      {!data ? (
        <div className="grid grid-cols-1 sm:grid-cols-2">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i} className="h-[76px] border-b border-border p-3 odd:sm:border-r">
              <Skeleton className="h-full" />
            </div>
          ))}
        </div>
      ) : data.length === 0 ? (
        <EmptyState
          icon={AtSign}
          title="Chưa có kênh nào"
          description="Thêm kênh TikTok của đối tác để bắt đầu theo dõi số liệu."
          action={
            can('partners:write') ? (
              <Button variant="secondary" className="mt-2" onClick={() => navigate('/channels?new=1')}>
                <AtSign className="h-4 w-4" aria-hidden />
                Thêm kênh
              </Button>
            ) : undefined
          }
        />
      ) : (
        <ul className="grid grid-cols-1 sm:grid-cols-2">
          {data.map((channel) => (
            <li key={channel.id} className="border-b border-border last:border-b-0 sm:odd:border-r sm:[&:nth-last-child(2):nth-child(odd)]:border-b-0">
              <Link
                to={`/channels/${channel.id}`}
                className="group flex h-[76px] items-center gap-3 px-4 hover:bg-surface"
              >
                <ChannelAvatar name={channel.displayName} tone={channel.tone} src={channel.avatarUrl} size={40} />
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-base leading-5">{channel.handle}</span>
                  <span className="mt-0.5 flex items-center gap-2 text-[13px] text-muted">
                    <span className="truncate">{channel.partnerName}</span>
                    <StatusBadge status={channel.status} className="shrink-0" />
                  </span>
                </span>
                <ArrowRight className="h-4 w-4 shrink-0 text-up" aria-hidden />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </Widget>
  );
}
