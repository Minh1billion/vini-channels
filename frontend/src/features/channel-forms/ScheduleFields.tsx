import { useState } from 'react';
import { CRON_PRESETS } from '@/entities/sync/cron';
import { SelectField, TextField } from '@/shared/ui';

const CUSTOM = 'custom';

interface Props {
  cron: string;
  timezone: string;
  onCronChange: (value: string) => void;
  onTimezoneChange: (value: string) => void;
}

export function ScheduleFields({ cron, timezone, onCronChange, onTimezoneChange }: Props) {
  const [custom, setCustom] = useState(cron !== '' && !CRON_PRESETS.some((preset) => preset.value === cron));

  const choose = (value: string) => {
    setCustom(value === CUSTOM);
    onCronChange(value === CUSTOM ? '' : value);
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <SelectField label="Lịch đồng bộ" value={custom ? CUSTOM : cron} onChange={(e) => choose(e.target.value)}>
          <option value="">Mặc định (hằng ngày lúc 08:00)</option>
          {CRON_PRESETS.map((preset) => (
            <option key={preset.value} value={preset.value}>
              {preset.label}
            </option>
          ))}
          <option value={CUSTOM}>Tùy chỉnh (cron)</option>
        </SelectField>
        <TextField label="Múi giờ" value={timezone} onChange={(e) => onTimezoneChange(e.target.value)} required />
      </div>
      {custom ? (
        <TextField
          label="Biểu thức cron"
          value={cron}
          onChange={(e) => onCronChange(e.target.value)}
          placeholder="0 */4 * * *"
          className="font-mono"
          hint="Năm trường: phút giờ ngày tháng thứ. Để trống để dùng lịch mặc định."
        />
      ) : null}
    </div>
  );
}
