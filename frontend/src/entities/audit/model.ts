import type { AuditAction } from './types';

export const actionLabels: Record<AuditAction, string> = {
  'partner.create': 'Tạo đối tác',
  'partner.update': 'Sửa đối tác',
  'partner.archive': 'Lưu trữ đối tác',
  'partner.restore': 'Khôi phục đối tác',
  'channel.register': 'Thêm kênh',
  'channel.update': 'Sửa kênh',
  'channel.schedule': 'Đổi lịch đồng bộ',
  'channel.archive': 'Lưu trữ kênh',
  'channel.restore': 'Khôi phục kênh',
  'channel.token': 'Nhập token kênh',
  'channel.token_revoked': 'Token kênh bị thu hồi',
  'provider.update': 'Cấu hình nguồn dữ liệu',
  'scoring.weights': 'Đổi trọng số điểm',
  'user.create': 'Tạo người dùng',
  'user.role': 'Đổi vai trò',
  'user.status': 'Đổi trạng thái người dùng',
  'user.password': 'Đổi mật khẩu',
};

export const actionOptions = Object.entries(actionLabels) as Array<[AuditAction, string]>;

const fieldLabels: Record<string, string> = {
  name: 'Tên',
  industry: 'Ngành',
  owner: 'Người phụ trách',
  logo_url: 'Logo',
  notes: 'Ghi chú',
  tags: 'Nhãn',
  display_name: 'Tên hiển thị',
  avatar_url: 'Ảnh đại diện',
  is_active: 'Hoạt động',
  schedule: 'Lịch',
  provider: 'Nguồn',
  partner_id: 'Đối tác',
  token: 'Token',
  enabled: 'Bật',
  priority: 'Ưu tiên',
  monthly_quota: 'Hạn mức tháng',
  credentials: 'Khóa API',
  engagement: 'Tương tác',
  growth: 'Tăng trưởng',
  reach: 'Tiếp cận',
  consistency: 'Đều đặn',
  role: 'Vai trò',
  password: 'Mật khẩu',
  reason: 'Lý do',
  by: 'Thực hiện',
};

const valueLabels: Record<string, string> = {
  changed: 'đã đổi',
  self: 'chính chủ',
  updated: 'đã cập nhật',
  cleared: 'đã xóa',
  provided: 'có',
  none: 'không',
  true: 'có',
  false: 'không',
  null: 'trống',
};

const formatValue = (value: string) =>
  value
    .split(' → ')
    .map((part) => valueLabels[part] ?? part)
    .join(' → ');

export const detailLines = (detail: Record<string, string>) =>
  Object.entries(detail).map(([key, value]) => `${fieldLabels[key] ?? key}: ${formatValue(value)}`);
