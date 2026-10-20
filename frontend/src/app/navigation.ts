import {
  AtSign,
  Clapperboard,
  FileText,
  Gauge,
  Handshake,
  LayoutDashboard,
  Plug,
  RefreshCw,
  ScrollText,
  Scale,
  Users,
  type LucideIcon,
} from 'lucide-react';

export type NavAlertKey = 'sync' | 'providers';

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
  alertKey?: NavAlertKey;
}

export const mainNav: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/partners', label: 'Đối tác', icon: Handshake },
  { to: '/channels', label: 'Kênh', icon: AtSign },
  { to: '/videos', label: 'Video', icon: Clapperboard },
  { to: '/compare', label: 'So sánh', icon: Scale },
  { to: '/sync', label: 'Đồng bộ', icon: RefreshCw, alertKey: 'sync' },
  { to: '/reports', label: 'Báo cáo', icon: FileText },
];

export const adminNav: NavItem[] = [
  { to: '/settings/providers', label: 'Nguồn dữ liệu', icon: Plug, alertKey: 'providers' },
  { to: '/settings/scoring', label: 'Điểm hiệu quả', icon: Gauge },
  { to: '/settings/users', label: 'Người dùng', icon: Users },
  { to: '/settings/audit', label: 'Nhật ký hoạt động', icon: ScrollText },
];

export const placeholderTitles: Record<string, string> = {
};
