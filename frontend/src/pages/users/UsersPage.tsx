import {
  Ban,
  BarChart3,
  CircleCheck,
  Eye,
  Handshake,
  KeyRound,
  ShieldCheck,
  ShieldOff,
  UserCheck,
  UserPlus,
  UserX,
  Users,
  type LucideIcon,
} from 'lucide-react';
import { useState } from 'react';
import { displayName, roleLabels } from '@/entities/user/model';
import type { Role, User } from '@/entities/user/types';
import { useAuth } from '@/features/auth/AuthProvider';
import { PasswordDialog } from '@/features/user-forms/PasswordDialog';
import { UserDialog } from '@/features/user-forms/UserDialog';
import { usersApi } from '@/shared/api';
import { cn } from '@/shared/lib/cn';
import { errorMessage } from '@/shared/lib/errors';
import { useAsync } from '@/shared/lib/useAsync';
import { Button, Chip, EmptyState, FormError, IconButton, SelectField, Skeleton, Widget } from '@/shared/ui';
import { PageHeader } from '@/widgets/page-header/PageHeader';

const ROLES: Role[] = ['admin', 'manager', 'analyst', 'viewer'];

const roleIcons: Record<Role, LucideIcon> = {
  admin: ShieldCheck,
  manager: Handshake,
  analyst: BarChart3,
  viewer: Eye,
};

function Stat({ icon: Icon, value, label }: { icon: LucideIcon; value: number; label: string }) {
  return (
    <div className="flex items-center gap-3 rounded-card border border-border bg-card px-4 py-3">
      <span aria-hidden className="flex h-9 w-9 items-center justify-center rounded-full bg-surface">
        <Icon className="h-4 w-4" strokeWidth={1.75} />
      </span>
      <div className="leading-tight">
        <p className="text-xl font-bold">{value}</p>
        <p className="text-xs text-muted">{label}</p>
      </div>
    </div>
  );
}

interface CardProps {
  user: User;
  isMe: boolean;
  onRole: (role: Role) => void;
  onReset: () => void;
  onToggle: () => void;
}

function UserCard({ user, isMe, onRole, onReset, onToggle }: CardProps) {
  const active = user.is_active;
  return (
    <li className={cn('flex flex-col gap-4 rounded-card border border-border bg-card p-4 transition-colors hover:bg-surface', !active && 'opacity-80')}>
      <div className="flex items-center gap-3">
        <span
          aria-hidden
          className={cn(
            'inline-flex h-12 w-12 shrink-0 select-none items-center justify-center rounded-full text-lg font-bold uppercase ring-1 ring-border',
            active ? 'bg-red text-[var(--on-red)]' : 'bg-surface text-muted',
          )}
        >
          {user.email.charAt(0)}
        </span>
        <div className="min-w-0 flex-1">
          <p className="flex items-center gap-2">
            <span className={cn('truncate font-bold', !active && 'text-muted')}>{displayName(user.email)}</span>
            {isMe ? <Chip className="h-6 shrink-0 px-2 text-xs">Bạn</Chip> : null}
          </p>
          <p className="truncate text-[13px] text-muted" title={user.email}>
            {user.email}
          </p>
        </div>
      </div>

      <SelectField
        label={`Vai trò của ${user.email}`}
        hideLabel
        icon={roleIcons[user.role]}
        value={user.role}
        disabled={isMe}
        onChange={(e) => onRole(e.target.value as Role)}
      >
        {ROLES.map((role) => (
          <option key={role} value={role}>
            {roleLabels[role]}
          </option>
        ))}
      </SelectField>

      <div className="mt-auto flex items-center justify-between gap-2 border-t border-border pt-3">
        <span className={cn('inline-flex items-center gap-1.5 text-[13px] font-medium', active ? 'text-blue' : 'text-muted')}>
          {active ? <CircleCheck className="h-4 w-4" aria-hidden /> : <Ban className="h-4 w-4" aria-hidden />}
          {active ? 'Hoạt động' : 'Đã vô hiệu'}
        </span>
        <span className="flex gap-1">
          <IconButton label="Đổi mật khẩu" bordered onClick={onReset}>
            <KeyRound className="h-4 w-4" aria-hidden />
          </IconButton>
          {isMe ? null : (
            <IconButton label={active ? 'Vô hiệu hóa' : 'Kích hoạt'} bordered onClick={onToggle}>
              {active ? <UserX className="h-4 w-4" aria-hidden /> : <UserCheck className="h-4 w-4" aria-hidden />}
            </IconButton>
          )}
        </span>
      </div>
    </li>
  );
}

function UsersTable() {
  const { user: me } = useAuth();
  const { data, loading, error, reload } = useAsync(() => usersApi.list(), []);
  const [creating, setCreating] = useState(false);
  const [resetting, setResetting] = useState<User | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const change = async (target: User, body: { role?: Role; is_active?: boolean }) => {
    setActionError(null);
    try {
      await usersApi.update(target.id, body);
      reload();
    } catch (err) {
      setActionError(errorMessage(err));
    }
  };

  const rows = data ?? [];
  const activeCount = rows.filter((row) => row.is_active).length;
  const adminCount = rows.filter((row) => row.role === 'admin').length;

  return (
    <>
      <PageHeader
        icon={Users}
        title="Người dùng"
        description="Quản lý tài khoản, vai trò và trạng thái truy cập."
        actions={
          <Button variant="primary" onClick={() => setCreating(true)}>
            <UserPlus className="h-4 w-4" aria-hidden />
            Thêm người dùng
          </Button>
        }
      />

      <FormError message={actionError} />

      {!data && loading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 3 }, (_, i) => (
            <Skeleton key={i} className="h-44" />
          ))}
        </div>
      ) : error ? (
        <Widget>
          <EmptyState
            icon={Users}
            title="Không tải được danh sách người dùng"
            description={errorMessage(error)}
            action={<Button variant="secondary" onClick={reload}>Thử lại</Button>}
          />
        </Widget>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-3 gap-3 sm:max-w-xl">
            <Stat icon={Users} value={rows.length} label="Tổng" />
            <Stat icon={CircleCheck} value={activeCount} label="Hoạt động" />
            <Stat icon={ShieldCheck} value={adminCount} label="Quản trị" />
          </div>
          <ul aria-label="Danh sách người dùng" className="m-0 grid list-none gap-4 p-0 sm:grid-cols-2 xl:grid-cols-3">
            {rows.map((row) => (
              <UserCard
                key={row.id}
                user={row}
                isMe={row.id === me?.id}
                onRole={(role) => change(row, { role })}
                onReset={() => setResetting(row)}
                onToggle={() => change(row, { is_active: !row.is_active })}
              />
            ))}
          </ul>
        </div>
      )}

      {creating ? (
        <UserDialog
          onClose={() => setCreating(false)}
          onSaved={() => {
            setCreating(false);
            reload();
          }}
        />
      ) : null}
      {resetting ? <PasswordDialog user={resetting} onClose={() => setResetting(null)} /> : null}
    </>
  );
}

export function UsersPage() {
  const { can } = useAuth();
  if (!can('users:write')) {
    return (
      <>
        <PageHeader
        icon={Users}
        title="Người dùng"
        description="Quản lý tài khoản, vai trò và trạng thái truy cập."
      />
        <Widget>
          <EmptyState icon={ShieldOff} title="Bạn không có quyền" description="Chỉ quản trị viên mới quản lý được tài khoản." />
        </Widget>
      </>
    );
  }
  return <UsersTable />;
}