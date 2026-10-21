export type NotificationKind =
  | 'sync_failures'
  | 'token_expiring'
  | 'engagement_drop'
  | 'job_succeeded'
  | 'job_failed';

export interface NotificationRecord {
  id: string;
  kind: NotificationKind;
  channel_id: string;
  title: string;
  message: string;
  created_at: string;
  read_at: string | null;
}

export interface PushConfig {
  enabled: boolean;
  public_key: string | null;
}

export interface PushSubscriptionInput {
  endpoint: string;
  p256dh: string;
  auth: string;
}

export interface NotificationList {
  items: NotificationRecord[];
  unread_count: number;
}
