import { Bell } from 'lucide-react';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { NotificationRecord } from '@/entities/notification/types';
import { notificationsApi } from '@/shared/api';
import { cn } from '@/shared/lib/cn';
import { relativeTime } from '@/shared/lib/format';
import { useAsync } from '@/shared/lib/useAsync';
import { IconButton, Menu } from '@/shared/ui';

const POLL_MS = 60_000;

export function NotificationBell({ onNavigate }: { onNavigate: () => void }) {
  const navigate = useNavigate();
  const notifications = useAsync(() => notificationsApi.list(), []);
  const { reload } = notifications;
  const items = notifications.data?.items ?? [];
  const unread = notifications.data?.unread_count ?? 0;

  useEffect(() => {
    const timer = window.setInterval(reload, POLL_MS);
    return () => window.clearInterval(timer);
  }, [reload]);

  const open = async (item: NotificationRecord, close: () => void) => {
    close();
    onNavigate();
    navigate(`/channels/${item.channel_id}`);
    if (!item.read_at) {
      await notificationsApi.markRead(item.id).catch(() => undefined);
      reload();
    }
  };

  const readAll = async () => {
    await notificationsApi.markAllRead().catch(() => undefined);
    reload();
  };

  return (
    <Menu
      align="start"
      className="w-80"
      trigger={({ open: isOpen, toggle }) => (
        <span className="relative inline-flex">
          <IconButton
            bordered
            label={unread > 0 ? `Thông báo (${unread} chưa đọc)` : 'Thông báo'}
            className="h-10 w-10"
            aria-haspopup="menu"
            aria-expanded={isOpen}
            onClick={() => {
              if (!isOpen) reload();
              toggle();
            }}
          >
            <Bell className="h-4 w-4" aria-hidden />
          </IconButton>
          {unread > 0 ? (
            <span
              aria-hidden
              className="pointer-events-none absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-fg px-1 text-[10px] font-medium text-bg"
            >
              {unread > 9 ? '9+' : unread}
            </span>
          ) : null}
        </span>
      )}
    >
      {(close) => (
        <div className="flex max-h-96 flex-col">
          <div className="flex items-center justify-between px-2.5 py-1.5">
            <span className="text-sm font-medium">Thông báo</span>
            <button
              type="button"
              disabled={unread === 0}
              onClick={readAll}
              className="text-[13px] font-medium text-blue underline-offset-4 hover:underline hover:decoration-blue disabled:text-muted disabled:no-underline"
            >
              Đánh dấu đã đọc
            </button>
          </div>
          <div className="overflow-y-auto">
            {items.length === 0 ? (
              <p className="px-2.5 py-4 text-sm text-muted">Chưa có thông báo nào.</p>
            ) : (
              items.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  role="menuitem"
                  onClick={() => open(item, close)}
                  className="flex w-full flex-col gap-0.5 rounded-field px-2.5 py-2 text-left hover:bg-surface"
                >
                  <span className="flex items-center gap-2">
                    {item.read_at ? null : <span className="h-2 w-2 shrink-0 rounded-full bg-fg" aria-hidden />}
                    <span className={cn('text-sm', !item.read_at && 'font-medium')}>{item.title}</span>
                  </span>
                  <span className="text-[13px] text-muted">{item.message}</span>
                  <time dateTime={item.created_at} className="text-xs text-muted">
                    {relativeTime(new Date(item.created_at))}
                  </time>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </Menu>
  );
}
