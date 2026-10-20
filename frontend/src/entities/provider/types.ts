export interface ProviderRecord {
  key: string;
  label: string;
  enabled: boolean;
  priority: number;
  monthly_quota: number | null;
  used_this_month: number;
  is_configured: boolean;
  credential_fields: string[];
  optional_fields: string[];
  requires_channel_token: boolean;
}
