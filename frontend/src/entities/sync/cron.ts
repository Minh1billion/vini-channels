export const CRON_PRESETS = [
  { value: '0 */6 * * *', label: 'Mỗi 6 giờ' },
  { value: '0 */12 * * *', label: 'Mỗi 12 giờ' },
  { value: '0 8 * * *', label: 'Hằng ngày lúc 08:00' },
  { value: '0 8 * * 1', label: 'Thứ Hai hằng tuần lúc 08:00' },
] as const;

export const describeCron = (cron: string) => CRON_PRESETS.find((preset) => preset.value === cron)?.label ?? null;
