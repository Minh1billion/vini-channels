const SOURCE_LABELS: Record<string, string> = {
  tiktok: 'TikTok',
  scrapecreators: 'ScrapeCreators',
  apify: 'Apify',
};

export const sourceLabel = (key: string | null) => (key ? (SOURCE_LABELS[key] ?? key) : '—');

export const credentialLabels: Record<string, string> = {
  api_key: 'Khóa API',
  api_token: 'Token API',
  actor_id: 'Actor ID',
  client_key: 'Client key',
  client_secret: 'Client secret',
};
