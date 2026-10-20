import { useState } from 'react';
import type { ChannelRecord } from '@/entities/channel/types';
import { channelsApi } from '@/shared/api';
import { CheckboxField, FormDialog, TextField } from '@/shared/ui';
import { ScheduleFields } from './ScheduleFields';

interface Props {
  channel: ChannelRecord;
  onClose: () => void;
  onSaved: () => void;
}

export function ChannelDialog({ channel, onClose, onSaved }: Props) {
  const [displayName, setDisplayName] = useState(channel.display_name);
  const [cron, setCron] = useState(channel.sync_cron ?? '');
  const [timezone, setTimezone] = useState(channel.timezone);
  const [isActive, setIsActive] = useState(channel.is_active);

  const submit = async () => {
    const cronValue = cron.trim() || null;
    if (displayName.trim() !== channel.display_name || isActive !== channel.is_active) {
      await channelsApi.update(channel.id, { display_name: displayName.trim(), is_active: isActive });
    }
    if (cronValue !== channel.sync_cron || timezone.trim() !== channel.timezone) {
      await channelsApi.setSchedule(channel.id, cronValue, timezone.trim());
    }
    onSaved();
  };

  return (
    <FormDialog
      title="Sửa kênh"
      description={`@${channel.handle}`}
      submitLabel="Lưu"
      canSubmit={Boolean(timezone.trim())}
      onSubmit={submit}
      onClose={onClose}
    >
      <TextField label="Tên hiển thị" value={displayName} onChange={(e) => setDisplayName(e.target.value)} autoFocus />
      <ScheduleFields cron={cron} timezone={timezone} onCronChange={setCron} onTimezoneChange={setTimezone} />
      <CheckboxField label="Đang theo dõi" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
    </FormDialog>
  );
}
