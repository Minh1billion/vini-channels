export type AuditAction =
  | 'partner.create'
  | 'partner.update'
  | 'partner.archive'
  | 'partner.restore'
  | 'channel.register'
  | 'channel.update'
  | 'channel.schedule'
  | 'channel.archive'
  | 'channel.restore'
  | 'channel.token'
  | 'channel.token_revoked'
  | 'provider.update'
  | 'scoring.weights'
  | 'user.create'
  | 'user.role'
  | 'user.status'
  | 'user.password';

export interface AuditEntry {
  id: string;
  actor_id: string;
  actor_email: string;
  action: AuditAction;
  target_type: string;
  target_id: string;
  target_label: string;
  detail: Record<string, string>;
  occurred_at: string;
}

export type AuditQuery = {
  actor_id?: string;
  action?: string;
  date_from?: string;
  date_to?: string;
  limit: number;
};
