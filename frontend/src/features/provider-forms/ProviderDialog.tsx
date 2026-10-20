import { useState } from 'react';
import { credentialLabels } from '@/entities/provider/labels';
import type { ProviderRecord } from '@/entities/provider/types';
import { providersApi, type ProviderUpdateInput } from '@/shared/api';
import { FormDialog, FormSection, TextField } from '@/shared/ui';

interface Props {
  provider: ProviderRecord;
  onClose: () => void;
  onSaved: () => void;
}

export function ProviderDialog({ provider, onClose, onSaved }: Props) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [quota, setQuota] = useState(provider.monthly_quota === null ? '' : String(provider.monthly_quota));

  const allOptional = provider.credential_fields.every((field) => provider.optional_fields.includes(field));
  const quotaText = quota.trim();
  const quotaInvalid = quotaText !== '' && !/^\d+$/.test(quotaText);

  const submit = async () => {
    const body: ProviderUpdateInput = { monthly_quota: quotaText === '' ? null : Number(quotaText) };
    const entered = Object.fromEntries(Object.entries(values).filter(([, value]) => value.trim() !== ''));
    if (Object.keys(entered).length > 0) body.credentials = entered;
    await providersApi.update(provider.key, body);
    onSaved();
  };

  return (
    <FormDialog
      title={`Cấu hình ${provider.label}`}
      submitLabel="Lưu"
      canSubmit={!quotaInvalid}
      onSubmit={submit}
      onClose={onClose}
    >
      {provider.credential_fields.length > 0 ? (
        <FormSection
          title="Khóa truy cập"
          description={
            allOptional
              ? 'Không bắt buộc, nhưng thiếu thì token kênh không được tự gia hạn. Khi đổi, nhập lại đủ cả hai trường.'
              : provider.is_configured
              ? 'Đã lưu khóa. Để trống nếu không muốn đổi; khi đổi, nhập lại đủ các trường bắt buộc.'
              : 'Chưa có khóa. Nhập để có thể bật nguồn này.'
          }
        >
          {provider.credential_fields.map((field) => (
            <TextField
              key={field}
              label={`${credentialLabels[field] ?? field}${provider.optional_fields.includes(field) ? ' (không bắt buộc)' : ''}`}
              type="password"
              autoComplete="off"
              value={values[field] ?? ''}
              onChange={(e) => setValues((current) => ({ ...current, [field]: e.target.value }))}
            />
          ))}
        </FormSection>
      ) : null}
      <TextField
        label="Hạn mức mỗi tháng (lượt gọi)"
        inputMode="numeric"
        value={quota}
        onChange={(e) => setQuota(e.target.value)}
        error={quotaInvalid ? 'Nhập số nguyên không âm' : undefined}
        hint={quotaInvalid ? undefined : 'Để trống nếu không giới hạn'}
      />
    </FormDialog>
  );
}
