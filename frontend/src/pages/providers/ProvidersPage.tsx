import { ChevronDown, ChevronUp, Plug, ShieldOff } from 'lucide-react';
import { useState } from 'react';
import { StatusBadge } from '@/entities/channel/StatusBadge';
import type { ChannelRecord } from '@/entities/channel/types';
import { ProviderLogo } from '@/entities/provider/ProviderLogo';
import type { ProviderRecord } from '@/entities/provider/types';
import { useAuth } from '@/features/auth/AuthProvider';
import { ChannelTokenDialog } from '@/features/channel-forms/ChannelTokenDialog';
import { ProviderDialog } from '@/features/provider-forms/ProviderDialog';
import { channelsApi, providersApi } from '@/shared/api';
import { errorMessage } from '@/shared/lib/errors';
import { full } from '@/shared/lib/format';
import { useAsync } from '@/shared/lib/useAsync';
import {
  Button,
  CheckboxField,
  Chip,
  DataTable,
  EmptyState,
  FormError,
  IconButton,
  ProgressBar,
  Skeleton,
  Widget,
  type Column,
} from '@/shared/ui';
import { PageHeader } from '@/widgets/page-header/PageHeader';

const PRIORITY_STEP = 10;

function Usage({ provider }: { provider: ProviderRecord }) {
  const { used_this_month: used, monthly_quota: quota } = provider;
  if (quota === null) {
    return <span className="text-[13px] text-muted">{full(used)} lượt tháng này · không giới hạn</span>;
  }
  const ratio = quota === 0 ? 100 : (used / quota) * 100;
  return (
    <span className="flex flex-col gap-1.5">
      <span className="text-[13px] text-muted">
        <span className="font-medium text-fg">{full(used)}</span> / {full(quota)} lượt tháng này
      </span>
      <ProgressBar value={ratio} label={`Mức dùng ${provider.label}`} />
    </span>
  );
}

function ProviderRow({
  provider,
  index,
  total,
  canWrite,
  busy,
  onMove,
  onToggle,
  onConfigure,
}: {
  provider: ProviderRecord;
  index: number;
  total: number;
  canWrite: boolean;
  busy: boolean;
  onMove: (delta: -1 | 1) => void;
  onToggle: (enabled: boolean) => void;
  onConfigure: () => void;
}) {
  return (
    <li className="flex flex-wrap items-center gap-x-4 gap-y-3 border-t border-border px-4 py-3 first:border-t-0">
      <span className="flex items-center gap-1">
        <span className="w-6 text-center font-medium text-muted">{index + 1}</span>
        {canWrite ? (
          <span className="flex flex-col">
            <IconButton label={`Đưa ${provider.label} lên`} size="sm" disabled={busy || index === 0} onClick={() => onMove(-1)}>
              <ChevronUp className="h-4 w-4" aria-hidden />
            </IconButton>
            <IconButton
              label={`Đưa ${provider.label} xuống`}
              size="sm"
              disabled={busy || index === total - 1}
              onClick={() => onMove(1)}
            >
              <ChevronDown className="h-4 w-4" aria-hidden />
            </IconButton>
          </span>
        ) : null}
      </span>

      <span className="min-w-[180px] flex-1">
        <span className="flex flex-wrap items-center gap-3">
          <ProviderLogo providerKey={provider.key} size={36} />
          <span className="font-medium">{provider.label}</span>
          {!provider.is_configured ? <Chip>Chưa có khóa</Chip> : null}
          {provider.requires_channel_token ? <Chip>Cần token theo kênh</Chip> : null}
        </span>
      </span>

      <span className="w-full min-w-[200px] sm:w-64">
        <Usage provider={provider} />
      </span>

      <span className="flex items-center gap-3">
        <CheckboxField
          label="Bật"
          checked={provider.enabled}
          disabled={!canWrite || busy}
          onChange={(e) => onToggle(e.target.checked)}
        />
        {canWrite ? (
          <Button variant="primary" size="sm" onClick={onConfigure}>
            Cấu hình
          </Button>
        ) : null}
      </span>
    </li>
  );
}

export function ProvidersPage() {
  const { can } = useAuth();
  const canRead = can('sync:read');
  const canWrite = can('providers:write');
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [configuring, setConfiguring] = useState<ProviderRecord | null>(null);
  const [tokenFor, setTokenFor] = useState<ChannelRecord | null>(null);

  const providers = useAsync(() => (canRead ? providersApi.list() : Promise.resolve([])), [canRead]);
  const channels = useAsync(() => (canRead ? channelsApi.list() : Promise.resolve([])), [canRead]);

  const run = async (action: () => Promise<unknown>) => {
    setBusy(true);
    setActionError(null);
    try {
      await action();
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setBusy(false);
      providers.reload();
    }
  };

  const toggle = (provider: ProviderRecord, enabled: boolean) =>
    run(() => providersApi.update(provider.key, { enabled }));

  const move = (index: number, delta: -1 | 1) => {
    const items = [...(providers.data ?? [])];
    const target = index + delta;
    if (target < 0 || target >= items.length) return;
    [items[index], items[target]] = [items[target], items[index]];
    return run(() =>
      Promise.all(
        items.flatMap((item, position) => {
          const priority = (position + 1) * PRIORITY_STEP;
          return item.priority === priority ? [] : [providersApi.update(item.key, { priority })];
        }),
      ),
    );
  };

  if (!canRead) {
    return (
      <>
        <PageHeader
        icon={Plug}
        title="Nguồn dữ liệu"
        description="Cấu hình nhà cung cấp dữ liệu và thứ tự ưu tiên khi lấy số liệu."
      />
        <Widget>
          <EmptyState icon={ShieldOff} title="Bạn không có quyền" description="Vai trò của bạn không xem được cấu hình nguồn dữ liệu." />
        </Widget>
      </>
    );
  }

  const channelColumns: Array<Column<ChannelRecord>> = [
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
    { key: 'mode', header: 'Kết nối', cell: (row) => (row.connection_mode === 'authorized' ? 'Ủy quyền' : 'Công khai') },
    { key: 'status', header: 'Trạng thái', cell: (row) => <StatusBadge status={row.status} /> },
  ];

  if (canWrite) {
    channelColumns.push({
      key: 'actions',
      header: '',
      align: 'right',
      cell: (row) => (
        <Button variant="secondary" size="sm" onClick={() => setTokenFor(row)}>
          {row.connection_mode === 'authorized' ? 'Đổi token' : 'Nhập token'}
        </Button>
      ),
    });
  }

  const list = providers.data;

  return (
    <>
      <PageHeader
        icon={Plug}
        title="Nguồn dữ liệu"
        description="Cấu hình nhà cung cấp dữ liệu và thứ tự ưu tiên khi lấy số liệu."
      />

      <FormError message={actionError} />

      <div className="flex flex-col gap-6">
        <Widget title="Thứ tự ưu tiên">
          {!list && providers.loading ? (
            <div className="flex flex-col gap-2 p-4">
              {Array.from({ length: 4 }, (_, i) => (
                <Skeleton key={i} className="h-14" />
              ))}
            </div>
          ) : providers.error ? (
            <EmptyState
              icon={Plug}
              title="Không tải được nguồn dữ liệu"
              description={errorMessage(providers.error)}
              action={<Button variant="secondary" onClick={providers.reload}>Thử lại</Button>}
            />
          ) : (
            <>
              <p className="px-4 pt-3 text-[13px] text-muted">
                Đồng bộ thử lần lượt từ trên xuống dưới, nguồn nào lỗi tạm thời hoặc hết hạn mức thì chuyển sang nguồn kế tiếp.
              </p>
              <ul>
                {(list ?? []).map((provider, index) => (
                  <ProviderRow
                    key={provider.key}
                    provider={provider}
                    index={index}
                    total={list?.length ?? 0}
                    canWrite={canWrite}
                    busy={busy}
                    onMove={(delta) => move(index, delta)}
                    onToggle={(enabled) => toggle(provider, enabled)}
                    onConfigure={() => setConfiguring(provider)}
                  />
                ))}
              </ul>
            </>
          )}
        </Widget>

        <Widget title="Token TikTok theo kênh">
          {!channels.data && channels.loading ? (
            <div className="flex flex-col gap-2 p-4">
              {Array.from({ length: 3 }, (_, i) => (
                <Skeleton key={i} className="h-10" />
              ))}
            </div>
          ) : channels.error ? (
            <EmptyState
              icon={Plug}
              title="Không tải được danh sách kênh"
              description={errorMessage(channels.error)}
              action={<Button variant="secondary" onClick={channels.reload}>Thử lại</Button>}
            />
          ) : channels.data && channels.data.length === 0 ? (
            <EmptyState icon={Plug} title="Chưa có kênh" description="Thêm kênh ở màn hình Kênh trước khi nhập token." />
          ) : (
            <DataTable
              caption="Token TikTok của từng kênh"
              columns={channelColumns}
              rows={channels.data ?? []}
              rowKey={(row) => row.id}
            />
          )}
        </Widget>
      </div>

      {configuring ? (
        <ProviderDialog
          provider={configuring}
          onClose={() => setConfiguring(null)}
          onSaved={() => {
            setConfiguring(null);
            providers.reload();
          }}
        />
      ) : null}
      {tokenFor ? (
        <ChannelTokenDialog
          channel={tokenFor}
          onClose={() => setTokenFor(null)}
          onSaved={() => {
            setTokenFor(null);
            channels.reload();
          }}
        />
      ) : null}
    </>
  );
}
