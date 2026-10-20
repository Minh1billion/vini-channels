export type ConnectionMode = 'authorized' | 'public';

export type ChannelStatus =
  | 'healthy'
  | 'token_expiring'
  | 'token_revoked'
  | 'not_found'
  | 'private'
  | 'provider_error';

export type AvatarTone = 'ink' | 'red' | 'cyan' | 'gray';

export interface Channel {
  id: string;
  handle: string;
  displayName: string;
  partnerName: string;
  status: ChannelStatus;
  mode: ConnectionMode;
  tone: AvatarTone;
  avatarUrl: string | null;
}

export interface ChannelRecord {
  id: string;
  partner_id: string;
  handle: string;
  display_name: string;
  avatar_url: string | null;
  connection_mode: ConnectionMode;
  status: ChannelStatus;
  sync_cron: string | null;
  timezone: string;
  is_active: boolean;
  archived_at: string | null;
}
