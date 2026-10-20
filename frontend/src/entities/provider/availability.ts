import type { ProviderRecord } from './types';

export function unavailableReason(provider: ProviderRecord, canManageTokens: boolean): string | null {
  if (!provider.enabled) return 'Đang tắt';
  if (!provider.is_configured) return 'Chưa có khóa API';
  if (provider.monthly_quota !== null && provider.used_this_month >= provider.monthly_quota) {
    return 'Đã hết hạn mức tháng này';
  }
  if (provider.requires_channel_token && !canManageTokens) return 'Cần quyền quản trị để nhập token';
  return null;
}
