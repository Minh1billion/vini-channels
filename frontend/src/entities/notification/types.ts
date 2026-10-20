export type NotificationKind = 'sync_failures' | 'token_expiring' | 'engagement_drop';

export interface NotificationRecord {
  id: string;
  kind: NotificationKind;
  channel_id: string;
  title: string;
  message: string;
  created_at: string;
  read_at: string | null;
}

export interface NotificationList {
  items: NotificationRecord[];
  unread_count: number;
}
