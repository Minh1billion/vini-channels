import { KeyRound, UserRound } from 'lucide-react';
import { useState } from 'react';
import { displayName, roleLabels } from '@/entities/user/model';
import { useAuth } from '@/features/auth/AuthProvider';
import { ChangePasswordDialog } from '@/features/user-forms/ChangePasswordDialog';
import { Button, Widget } from '@/shared/ui';
import { PageHeader } from '@/widgets/page-header/PageHeader';

export function ProfilePage() {
  const { user } = useAuth();
  const [changing, setChanging] = useState(false);
  const [done, setDone] = useState(false);
  if (!user) return null;

  return (
    <>
      <PageHeader
        icon={UserRound}
        title="Hồ sơ cá nhân"
        description="Thông tin tài khoản và bảo mật của bạn."
        actions={
          <Button
            variant="primary"
            onClick={() => {
              setDone(false);
              setChanging(true);
            }}
          >
            <KeyRound className="h-4 w-4" aria-hidden />
            Đổi mật khẩu
          </Button>
        }
      />
      <div className="flex flex-col gap-6">
        {done ? (
          <p role="status" className="text-sm text-blue">
            Đã đổi mật khẩu.
          </p>
        ) : null}
        <Widget title="Thông tin tài khoản" bodyClassName="p-4">
          <dl className="grid max-w-md grid-cols-[120px_1fr] gap-x-4 gap-y-3 text-sm">
            <dt className="text-muted">Tên hiển thị</dt>
            <dd className="font-medium">{displayName(user.email)}</dd>
            <dt className="text-muted">Email</dt>
            <dd className="break-all">{user.email}</dd>
            <dt className="text-muted">Vai trò</dt>
            <dd>{roleLabels[user.role]}</dd>
          </dl>
        </Widget>
      </div>
      {changing ? (
        <ChangePasswordDialog
          onClose={() => setChanging(false)}
          onSaved={() => {
            setChanging(false);
            setDone(true);
          }}
        />
      ) : null}
    </>
  );
}
