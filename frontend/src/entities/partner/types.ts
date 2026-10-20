export interface Partner {
  id: string;
  name: string;
  industry: string | null;
  owner_user_id: string | null;
  logo_url: string | null;
  notes: string;
  tags: string[];
  archived_at: string | null;
  channel_count: number;
}
