import type { Channel, ChannelRecord } from '@/entities/channel/types';
import { toneFor } from '@/entities/channel/tone';
import type { AttentionItem, DashboardData } from '@/entities/dashboard/types';
import type { Partner } from '@/entities/partner/types';
import type { SyncHealth, SyncRunRecord } from '@/entities/sync/types';
import { analyticsApi } from './analytics';
import { channelsApi } from './channels';
import { partnersApi } from './partners';
import { syncApi } from './sync';
import { lastDays } from '@/shared/lib/period';

const ATTENTION: Partial<Record<ChannelRecord['status'], { kind: AttentionItem['kind']; message: string }>> = {
  token_revoked: { kind: 'revoked', message: 'Chủ kênh đã thu hồi quyền truy cập' },
  token_expiring: { kind: 'expiring', message: 'Token sắp hết hạn' },
  provider_error: { kind: 'failing', message: 'Nguồn dữ liệu báo lỗi' },
  not_found: { kind: 'failing', message: 'Không tìm thấy kênh trên TikTok' },
  private: { kind: 'failing', message: 'Kênh đã chuyển sang riêng tư' },
};

const OVERVIEW_DAYS = 30;
const RECENT_CHANNELS = 4;
const RECENT_RUNS = 7;
const HEALTH_DOTS = 40;
const RUNS_FETCHED = 200;

function toChannel(record: ChannelRecord, partner: Partner | undefined): Channel {
  const handle = `@${record.handle}`;
  return {
    id: record.id,
    handle,
    displayName: record.display_name || handle,
    partnerName: partner?.name ?? '—',
    status: record.status,
    mode: record.connection_mode,
    tone: toneFor(record.id),
    avatarUrl: record.avatar_url,
  };
}

function buildHealth(runs: SyncRunRecord[], now: Date): SyncHealth {
  const finished = runs
    .filter((run) => run.status !== 'running')
    .filter((run) => {
      const started = new Date(run.started_at);
      return started.getFullYear() === now.getFullYear() && started.getMonth() === now.getMonth();
    })
    .sort((a, b) => a.started_at.localeCompare(b.started_at));
  const marks = finished.map((run) => (run.status === 'failed' ? ('failed' as const) : ('ok' as const)));
  return {
    month: now,
    ok: marks.filter((mark) => mark === 'ok').length,
    total: marks.length,
    runs: marks.slice(-HEALTH_DOTS),
  };
}

export const dashboardApi = {
  async load(options: { includeSync: boolean }): Promise<DashboardData> {
    const [overview, records, partners, runs, schedules] = await Promise.all([
      analyticsApi.overview(lastDays(OVERVIEW_DAYS)),
      channelsApi.list(),
      partnersApi.list(),
      options.includeSync ? syncApi.runs({ limit: RUNS_FETCHED }) : Promise.resolve(null),
      options.includeSync ? syncApi.schedules() : Promise.resolve(null),
    ]);
    const partnerById = new Map(partners.map((partner) => [partner.id, partner]));
    const attention: AttentionItem[] = records.flatMap((record) => {
      const rule = ATTENTION[record.status];
      if (!rule) return [];
      return [{ id: record.id, kind: rule.kind, handle: `@${record.handle}`, tone: toneFor(record.id), avatarUrl: record.avatar_url, message: rule.message }];
    });

    return {
      overview,
      counts: { partners: partners.length, channels: records.length },
      recent: records.slice(0, RECENT_CHANNELS).map((record) => toChannel(record, partnerById.get(record.partner_id))),
      connection: {
        expiring: records.filter((record) => record.status === 'token_expiring').length,
        revoked: records.filter((record) => record.status === 'token_revoked').length,
      },
      attention,
      sync:
        runs && schedules
          ? { health: buildHealth(runs, new Date()), runs: runs.slice(0, RECENT_RUNS), schedules }
          : undefined,
    };
  },
};
