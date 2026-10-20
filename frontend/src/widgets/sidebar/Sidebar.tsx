import {
  ChevronDown,
  ChevronsLeft,
  ChevronsRight,
  LogOut,
  Settings,
  UserRound,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { adminNav, mainNav, type NavAlertKey, type NavItem } from '@/app/navigation';
import { ChannelAvatar } from '@/entities/channel/ChannelAvatar';
import { ProviderLogo } from '@/entities/provider/ProviderLogo';
import { displayName, roleLabels } from '@/entities/user/model';
import { useAuth } from '@/features/auth/AuthProvider';
import { SearchBox } from '@/features/global-search/SearchBox';
import { ThemeToggle } from '@/features/theme-toggle/ThemeToggle';
import { unavailableReason } from '@/entities/provider/availability';
import { channelsApi, providersApi } from '@/shared/api';
import { cn } from '@/shared/lib/cn';
import { full } from '@/shared/lib/format';
import { useAsync } from '@/shared/lib/useAsync';
import { NotificationBell } from '@/widgets/notification-bell/NotificationBell';
import { BrandMark, Button, IconButton, Menu, MenuItem, MenuSeparator, ProgressBar } from '@/shared/ui';

interface Props {
  collapsed: boolean;
  onToggleCollapsed: () => void;
  onNavigate: () => void;
}

function NavRow({
  item,
  collapsed,
  onNavigate,
  size = 'lg',
  alert = 0,
}: {
  item: NavItem;
  collapsed: boolean;
  onNavigate: () => void;
  size?: 'lg' | 'md';
  alert?: number;
}) {
  const Icon = item.icon;
  const large = size === 'lg';
  return (
    <NavLink
      to={item.to}
      end={item.end}
      title={collapsed ? item.label : undefined}
      aria-label={alert > 0 ? `${item.label} (${alert} mục cần xử lý)` : undefined}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          'relative flex items-center gap-3 rounded-field px-2.5 transition-colors hover:bg-surface',
          large ? 'h-10 text-[15px] font-semibold' : 'h-9 text-sm font-medium',
          collapsed && 'justify-center px-0',
          isActive ? 'bg-surface font-bold text-red' : 'text-fg',
        )
      }
    >
      {({ isActive }) => (
        <>
          <Icon
            className="h-5 w-5 shrink-0"
            strokeWidth={isActive ? 2.25 : 2}
            fill={isActive ? 'currentColor' : 'none'}
            fillOpacity={isActive ? 0.2 : 0}
            aria-hidden
          />
          {collapsed ? <span className="sr-only">{item.label}</span> : <span className="truncate">{item.label}</span>}
          {alert > 0 ? (
            collapsed ? (
              <span aria-hidden className="absolute right-2 top-2 h-2.5 w-2.5 rounded-full bg-red ring-2 ring-bg" />
            ) : (
              <span
                aria-hidden
                className="ml-auto flex h-5 min-w-5 items-center justify-center rounded-full bg-red px-1.5 text-[11px] font-bold leading-none text-[var(--on-red)]"
              >
                {alert > 9 ? '9+' : alert}
              </span>
            )
          ) : null}
        </>
      )}
    </NavLink>
  );
}

export function Sidebar({ collapsed, onToggleCollapsed, onNavigate }: Props) {
  const [adminOpen, setAdminOpen] = useState(true);
  const { user, logout, can } = useAuth();
  const canReadSync = can('sync:read');
  const providers = useAsync(
    () => (canReadSync ? providersApi.list() : Promise.resolve([])),
    [canReadSync],
  );
  const enabledProviders = (providers.data ?? []).filter((provider) => provider.enabled);
  const channels = useAsync(
    () => (canReadSync ? channelsApi.list() : Promise.resolve([])),
    [canReadSync],
  );
  const { reload: reloadChannels } = channels;
  const { reload: reloadProviders } = providers;
  const location = useLocation();

  useEffect(() => {
    reloadChannels();
    reloadProviders();
  }, [location.pathname, reloadChannels, reloadProviders]);

  const alerts: Record<NavAlertKey, number> = {
    sync: (channels.data ?? []).filter((channel) => channel.status !== 'healthy' && channel.archived_at === null).length,
    providers: providers.data
      ? providers.data.filter((provider) => provider.enabled && unavailableReason(provider, true) !== null).length +
        (enabledProviders.length === 0 ? 1 : 0)
      : 0,
  };
  const alertFor = (item: NavItem) => (canReadSync && item.alertKey ? alerts[item.alertKey] : 0);
  const name = user ? displayName(user.email) : '';
  const roleLabel = user ? roleLabels[user.role] : '';
  const navigate = useNavigate();

  return (
    <div className="flex h-full flex-col bg-bg">
      <div className="flex flex-col gap-3 p-3">
        <Menu
          align="start"
          className="w-60"
          trigger={({ open, toggle }) => (
            <button
              type="button"
              aria-haspopup="menu"
              aria-expanded={open}
              onClick={toggle}
              className={cn(
                'flex w-full items-center gap-3 rounded-field p-1 text-left transition-colors hover:bg-surface',
                collapsed && 'justify-center',
              )}
            >
              <ChannelAvatar name={name || '?'} tone="ink" size={40} />
              {collapsed ? <span className="sr-only">Tài khoản của {name}</span> : (
                <>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium leading-5">{name}</span>
                    <span className="block truncate text-xs leading-4 text-muted">{roleLabel}</span>
                  </span>
                  <ChevronDown className="h-4 w-4 shrink-0 text-muted" aria-hidden />
                </>
              )}
            </button>
          )}
        >
          {(close) => (
            <>
              <MenuItem icon={UserRound} onSelect={() => { close(); onNavigate(); navigate('/profile'); }}>Hồ sơ cá nhân</MenuItem>
              <MenuItem icon={Settings} onSelect={close}>Tùy chọn hiển thị</MenuItem>
              <MenuSeparator />
              <MenuItem icon={LogOut} onSelect={() => { close(); void logout(); }}>Đăng xuất</MenuItem>
            </>
          )}
        </Menu>

        {collapsed ? (
          <div className="flex flex-col items-center gap-2">
            <SearchBox variant="icon" onNavigate={onNavigate} />
            <NotificationBell onNavigate={onNavigate} />
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <SearchBox appearance="pill" className="flex-1" onNavigate={onNavigate} />
            <NotificationBell onNavigate={onNavigate} />
          </div>
        )}
      </div>

      <div className="border-t border-border" />

      <nav aria-label="Điều hướng chính" className="flex-1 overflow-y-auto p-3">
        <ul className="flex flex-col gap-1">
          {mainNav.map((item) => (
            <li key={item.to}>
              <NavRow item={item} collapsed={collapsed} onNavigate={onNavigate} alert={alertFor(item)} />
            </li>
          ))}
        </ul>

        {!collapsed ? (
          <div className="mt-4">
            <button
              type="button"
              aria-expanded={adminOpen}
              onClick={() => setAdminOpen((value) => !value)}
              className="flex h-9 w-full items-center justify-between rounded-field px-2.5 text-[13px] font-bold text-muted hover:bg-surface"
            >
              Quản trị
              <ChevronDown className={cn('h-4 w-4 transition-transform', adminOpen && 'rotate-180')} aria-hidden />
            </button>
            {adminOpen ? (
              <ul className="mt-0.5 flex animate-rise flex-col gap-1">
                {adminNav.map((item) => (
                  <li key={item.to}>
                    <NavRow item={item} collapsed={false} onNavigate={onNavigate} size="md" alert={alertFor(item)} />
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ) : (
          <ul className="mt-3 flex flex-col gap-1 border-t border-border pt-3">
            {adminNav.map((item) => (
              <li key={item.to}>
                <NavRow item={item} collapsed onNavigate={onNavigate} size="md" alert={alertFor(item)} />
              </li>
            ))}
          </ul>
        )}
      </nav>

      {!collapsed && canReadSync ? (
        <div className="flex flex-col gap-3 border-t border-border p-4">
          {providers.data && enabledProviders.length === 0 ? (
            <>
              <div>
                <p className="text-sm font-medium">Chưa bật nguồn dữ liệu</p>
                <p className="mt-0.5 text-[13px] text-muted">Bật một nguồn để bắt đầu đồng bộ kênh.</p>
              </div>
              {can('providers:write') ? (
                <Link
                  to="/settings/providers"
                  onClick={onNavigate}
                  className="inline-flex items-center gap-1.5 text-sm font-medium text-blue underline-offset-4 hover:underline hover:decoration-blue"
                >
                  Cấu hình nguồn dữ liệu
                  <span aria-hidden>→</span>
                </Link>
              ) : null}
            </>
          ) : (
            <>
              <p className="text-[13px] text-muted">Lượt gọi nguồn tháng này</p>
              <ul className="flex flex-col gap-3 text-[13px]">
                {enabledProviders.map((provider) => (
                  <li key={provider.key} className="flex flex-col gap-1.5">
                    <span className="flex items-center justify-between">
                      <span className="flex items-center gap-2 text-muted">
                        <ProviderLogo providerKey={provider.key} size={20} />
                        {provider.label}
                      </span>
                      <span>
                        <span className="font-medium">{full(provider.used_this_month)}</span>
                        {provider.monthly_quota === null ? null : ` / ${full(provider.monthly_quota)}`}
                      </span>
                    </span>
                    {provider.monthly_quota === null ? null : (
                      <ProgressBar
                        value={provider.monthly_quota === 0 ? 100 : (provider.used_this_month / provider.monthly_quota) * 100}
                        label={`Hạn mức ${provider.label} đã dùng`}
                      />
                    )}
                  </li>
                ))}
              </ul>
              <Button variant="secondary" className="w-full justify-between" onClick={() => { onNavigate(); navigate('/settings/providers'); }}>
                <span>Quản lý hạn mức</span>
                <span aria-hidden>→</span>
              </Button>
            </>
          )}
        </div>
      ) : null}

      <div className={cn('flex items-center gap-2 border-t border-border p-3', collapsed ? 'flex-col' : 'justify-between')}>
        <Link to="/" aria-label="ViniChannels" onClick={onNavigate} className="flex items-center gap-2 rounded-field">
          <BrandMark size={28} />
          {collapsed ? null : <span className="text-sm font-bold">ViniChannels</span>}
        </Link>
        <div className={cn('flex items-center gap-1.5', collapsed && 'flex-col')}>
          <ThemeToggle />
          <IconButton
            bordered
            label={collapsed ? 'Mở rộng thanh bên' : 'Thu gọn thanh bên'}
            onClick={onToggleCollapsed}
            className="hidden lg:inline-flex"
          >
            {collapsed ? <ChevronsRight className="h-4 w-4" aria-hidden /> : <ChevronsLeft className="h-4 w-4" aria-hidden />}
          </IconButton>
        </div>
      </div>
    </div>
  );
}
