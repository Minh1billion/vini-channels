import { useMemo, useState } from 'react';
import type { Partner } from '@/entities/partner/types';
import { unavailableReason } from '@/entities/provider/availability';
import { useAuth } from '@/features/auth/AuthProvider';
import { channelsApi, providersApi } from '@/shared/api';
import { errorMessage } from '@/shared/lib/errors';
import { full } from '@/shared/lib/format';
import { useAsync } from '@/shared/lib/useAsync';
import { FormDialog, FormSection, OptionCardGroup, SelectField, Skeleton, TextField, type Option } from '@/shared/ui';
import { ScheduleFields } from './ScheduleFields';

const DEFAULT_TIMEZONE = 'Asia/Ho_Chi_Minh';

interface Props {
  partners: Partner[];
  onClose: () => void;
  onSaved: () => void;
}

export function AddChannelDialog({ partners, onClose, onSaved }: Props) {
  const { can } = useAuth();
  const canManageTokens = can('providers:write');
  const activePartners = partners.filter((partner) => partner.archived_at === null);
  const providers = useAsync(() => providersApi.list(), []);

  const [partnerId, setPartnerId] = useState(activePartners[0]?.id ?? '');
  const [handle, setHandle] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [chosen, setChosen] = useState('');
  const [cron, setCron] = useState('');
  const [timezone, setTimezone] = useState(DEFAULT_TIMEZONE);
  const [accessToken, setAccessToken] = useState('');
  const [refreshToken, setRefreshToken] = useState('');
  const [expiresAt, setExpiresAt] = useState('');

  const options = useMemo<Array<Option<string>>>(
    () =>
      (providers.data ?? []).map((provider) => ({
        value: provider.key,
        label: provider.label,
        disabledReason: unavailableReason(provider, canManageTokens) ?? undefined,
        description:
          provider.monthly_quota === null
            ? `${full(provider.used_this_month)} lượt tháng này`
            : `${full(provider.used_this_month)} / ${full(provider.monthly_quota)} lượt tháng này`,
      })),
    [providers.data, canManageTokens],
  );

  const selectable = options.filter((option) => !option.disabledReason);
  const providerKey = options.some((option) => option.value === chosen && !option.disabledReason)
    ? chosen
    : (selectable[0]?.value ?? '');
  const provider = providers.data?.find((item) => item.key === providerKey);
  const needsToken = provider?.requires_channel_token ?? false;

  const expiry = expiresAt ? new Date(expiresAt) : null;
  const tokenReady = !needsToken || (accessToken.trim() !== '' && expiry !== null && !Number.isNaN(expiry.getTime()));
  const canSubmit = Boolean(partnerId && handle.trim() && providerKey && tokenReady);

  const submit = async () => {
    await channelsApi.create({
      partner_id: partnerId,
      handle: handle.trim(),
      provider: providerKey,
      display_name: displayName.trim(),
      sync_cron: cron.trim() || null,
      timezone: timezone.trim(),
      token:
        needsToken && expiry
          ? {
              access_token: accessToken.trim(),
              refresh_token: refreshToken.trim() || null,
              expires_at: expiry.toISOString(),
            }
          : undefined,
    });
    onSaved();
  };

  return (
    <FormDialog
      title="Thêm kênh"
      description="Kênh chỉ được thêm khi nguồn dữ liệu đã chọn đọc được kênh này."
      size="lg"
      submitLabel="Kiểm tra và thêm kênh"
      pendingLabel="Đang kiểm tra kênh..."
      pendingNote={`Đang lấy dữ liệu @${handle.trim().replace(/^@/, '')} từ ${provider?.label ?? 'nguồn dữ liệu'}, có thể mất vài chục giây.`}
      canSubmit={canSubmit}
      onSubmit={submit}
      onClose={onClose}
    >
      <FormSection title="Kênh">
        <SelectField label="Đối tác" value={partnerId} onChange={(e) => setPartnerId(e.target.value)} required>
          {activePartners.length === 0 ? <option value="">Chưa có đối tác</option> : null}
          {activePartners.map((partner) => (
            <option key={partner.id} value={partner.id}>
              {partner.name}
            </option>
          ))}
        </SelectField>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField
            label="Handle TikTok"
            value={handle}
            onChange={(e) => setHandle(e.target.value)}
            placeholder="@ten.kenh"
            required
            autoFocus
          />
          <TextField
            label="Tên hiển thị"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            hint="Để trống để lấy từ TikTok"
          />
        </div>
      </FormSection>

      <FormSection title="Nguồn dữ liệu" description="Dùng để kiểm tra kênh và lấy dữ liệu lần đầu.">
        {providers.loading && !providers.data ? (
          <Skeleton className="h-20" />
        ) : providers.error ? (
          <p role="alert" className="text-sm text-down">
            {errorMessage(providers.error)}
          </p>
        ) : (
          <>
            <OptionCardGroup label="Chọn nguồn" value={providerKey} options={options} onChange={setChosen} />
            {selectable.length === 0 ? (
              <p className="text-sm text-down">
                Chưa có nguồn nào sẵn sàng. Bật hoặc cấu hình nguồn ở màn hình Nguồn dữ liệu.
              </p>
            ) : null}
          </>
        )}
        {needsToken ? (
          <div className="flex flex-col gap-4 border-t border-border pt-3">
            <TextField
              label="Access token của kênh"
              type="password"
              autoComplete="off"
              value={accessToken}
              onChange={(e) => setAccessToken(e.target.value)}
              required
            />
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <TextField
                label="Refresh token (không bắt buộc)"
                type="password"
                autoComplete="off"
                value={refreshToken}
                onChange={(e) => setRefreshToken(e.target.value)}
              />
              <TextField
                label="Token hết hạn lúc"
                type="datetime-local"
                value={expiresAt}
                onChange={(e) => setExpiresAt(e.target.value)}
                required
              />
            </div>
          </div>
        ) : null}
      </FormSection>

      <FormSection title="Lịch đồng bộ">
        <ScheduleFields cron={cron} timezone={timezone} onCronChange={setCron} onTimezoneChange={setTimezone} />
      </FormSection>
    </FormDialog>
  );
}
