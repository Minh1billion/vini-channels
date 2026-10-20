import { Gauge, ShieldOff } from 'lucide-react';
import { useEffect, useState } from 'react';
import {
  scoreComponents,
  type ChannelScore,
  type PartnerScore,
  type ScoreComponent,
  type ScoreWeights,
} from '@/entities/scoring/types';
import { useAuth } from '@/features/auth/AuthProvider';
import { scoringApi } from '@/shared/api';
import { RangePicker } from '@/features/period-picker/RangePicker';
import { errorMessage } from '@/shared/lib/errors';
import { lastDays, periodKey, type Period } from '@/shared/lib/period';
import { useAsync } from '@/shared/lib/useAsync';
import {
  Button,
  DataTable,
  EmptyState,
  FormError,
  ProgressBar,
  Skeleton,
  TextField,
  Widget,
  type Column,
} from '@/shared/ui';
import { PageHeader } from '@/widgets/page-header/PageHeader';

type Draft = Record<ScoreComponent, string>;

const toDraft = (weights: ScoreWeights): Draft => ({
  engagement: String(Math.round(weights.engagement * 100)),
  growth: String(Math.round(weights.growth * 100)),
  reach: String(Math.round(weights.reach * 100)),
  consistency: String(Math.round(weights.consistency * 100)),
});

const draftTotal = (draft: Draft) =>
  scoreComponents.reduce((sum, { key }) => sum + (Number(draft[key]) || 0), 0);

const isValidDraft = (draft: Draft) =>
  scoreComponents.every(({ key }) => draft[key] !== '' && Number(draft[key]) >= 0) && draftTotal(draft) === 100;

const score = (value: number | null) => (value === null ? '—' : value.toFixed(1).replace('.', ','));

function ScoreCell({ value, label }: { value: number | null; label: string }) {
  return (
    <span className="flex min-w-[120px] flex-col gap-1.5">
      <span className="font-medium">{score(value)}</span>
      <ProgressBar value={value ?? 0} label={label} />
    </span>
  );
}

function WeightsEditor({
  weights,
  canWrite,
  onSaved,
}: {
  weights: ScoreWeights;
  canWrite: boolean;
  onSaved: () => void;
}) {
  const [draft, setDraft] = useState<Draft>(toDraft(weights));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => setDraft(toDraft(weights)), [weights]);

  const total = draftTotal(draft);
  const saved = toDraft(weights);
  const changed = scoreComponents.some(({ key }) => draft[key] !== saved[key]);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await scoringApi.updateWeights({
        engagement: Number(draft.engagement) / 100,
        growth: Number(draft.growth) / 100,
        reach: Number(draft.reach) / 100,
        consistency: Number(draft.consistency) / 100,
      });
      onSaved();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 p-4">
      <p className="text-[13px] text-muted">
        Điểm của kênh là trung bình có trọng số của thứ hạng phần trăm ở bốn thành phần. Tổng trọng số phải bằng 100%.
      </p>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {scoreComponents.map(({ key, label, hint }) => (
          <TextField
            key={key}
            label={`${label} (%)`}
            hint={hint}
            type="number"
            inputMode="numeric"
            min={0}
            max={100}
            step={1}
            value={draft[key]}
            disabled={!canWrite || saving}
            onChange={(event) => setDraft((current) => ({ ...current, [key]: event.target.value }))}
          />
        ))}
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <span className={total === 100 ? 'text-sm text-muted' : 'text-sm text-down'}>Tổng: {total}%</span>
        {canWrite ? (
          <>
            <Button variant="primary" disabled={saving || !changed || !isValidDraft(draft)} onClick={save}>
              Lưu trọng số
            </Button>
            <Button disabled={saving || !changed} onClick={() => setDraft(saved)}>
              Hoàn tác
            </Button>
          </>
        ) : null}
      </div>
      <FormError message={error} />
    </div>
  );
}

const partnerColumns: Array<Column<PartnerScore>> = [
  { key: 'rank', header: '#', cell: (row) => row.rank ?? '—', className: 'w-12' },
  { key: 'name', header: 'Đối tác', cell: (row) => <span className="font-medium">{row.name}</span> },
  {
    key: 'channels',
    header: 'Kênh được chấm',
    cell: (row) => `${row.scored_channel_count} / ${row.channel_count}`,
  },
  { key: 'total', header: 'Điểm', cell: (row) => <ScoreCell value={row.total} label={`Điểm ${row.name}`} /> },
];

const channelColumns: Array<Column<ChannelScore>> = [
  { key: 'rank', header: '#', cell: (row) => row.rank ?? '—', className: 'w-12' },
  {
    key: 'channel',
    header: 'Kênh',
    cell: (row) => (
      <span className="flex flex-col py-1">
        <span className="font-medium">{row.display_name || `@${row.handle}`}</span>
        <span className="font-mono text-xs text-muted">@{row.handle}</span>
      </span>
    ),
  },
  { key: 'partner', header: 'Đối tác', cell: (row) => row.partner_name },
  { key: 'total', header: 'Điểm', cell: (row) => <ScoreCell value={row.total} label={`Điểm @${row.handle}`} /> },
  ...scoreComponents.map(({ key, label }) => ({
    key,
    header: label,
    align: 'right' as const,
    cell: (row: ChannelScore) => score(row.components[key]),
  })),
];

export function ScoringPage() {
  const { can } = useAuth();
  const canRead = can('scoring:read');
  const canWrite = can('scoring:write');
  const [period, setPeriod] = useState<Period>(lastDays(30));
  const periodId = periodKey(period);
  const board = useAsync(
    () => (canRead ? scoringApi.scoreboard(period) : Promise.resolve(undefined)),
    [canRead, periodId],
  );

  if (!canRead) {
    return (
      <>
        <PageHeader
        icon={Gauge}
        title="Điểm hiệu quả"
        description="Bảng xếp hạng điểm hiệu quả của các kênh trong kỳ đã chọn."
      />
        <Widget>
          <EmptyState icon={ShieldOff} title="Bạn không có quyền" description="Vai trò của bạn không xem được điểm hiệu quả." />
        </Widget>
      </>
    );
  }

  const data = board.data;

  return (
    <>
      <PageHeader
        icon={Gauge}
        title="Điểm hiệu quả"
        description="Bảng xếp hạng điểm hiệu quả của các kênh trong kỳ đã chọn."
      />
      <div className="mb-4">
        <RangePicker value={period} onChange={setPeriod} />
      </div>

      {!data && board.loading ? (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 4 }, (_, i) => (
            <Skeleton key={i} className="h-16" />
          ))}
        </div>
      ) : board.error || !data ? (
        <Widget>
          <EmptyState
            icon={Gauge}
            title="Không tải được điểm hiệu quả"
            description={errorMessage(board.error)}
            action={<Button variant="secondary" onClick={board.reload}>Thử lại</Button>}
          />
        </Widget>
      ) : (
        <div className="flex flex-col gap-6">
          <Widget title="Trọng số">
            <WeightsEditor weights={data.weights} canWrite={canWrite} onSaved={board.reload} />
          </Widget>
          <Widget title="Xếp hạng đối tác">
            {data.partners.length === 0 ? (
              <EmptyState icon={Gauge} title="Chưa có đối tác" description="Thêm đối tác và kênh để có điểm." />
            ) : (
              <DataTable caption="Xếp hạng đối tác theo điểm trung bình" columns={partnerColumns} rows={data.partners} rowKey={(row) => row.partner_id} />
            )}
          </Widget>
          <Widget title="Điểm theo kênh">
            {data.channels.length === 0 ? (
              <EmptyState icon={Gauge} title="Chưa có kênh" description="Thêm kênh và đồng bộ dữ liệu để có điểm." />
            ) : (
              <DataTable caption="Điểm hiệu quả của từng kênh" columns={channelColumns} rows={data.channels} rowKey={(row) => row.channel_id} />
            )}
          </Widget>
        </div>
      )}
    </>
  );
}
