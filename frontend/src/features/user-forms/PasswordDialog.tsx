import { useState } from 'react';
import type { User } from '@/entities/user/types';
import { usersApi } from '@/shared/api';
import { FormDialog, TextField } from '@/shared/ui';

interface Props {
  user: User;
  onClose: () => void;
}

export function PasswordDialog({ user, onClose }: Props) {
  const [password, setPassword] = useState('');

  const submit = async () => {
    await usersApi.update(user.id, { password });
    onClose();
  };

  return (
    <FormDialog
      title="Đổi mật khẩu"
      description={user.email}
      size="sm"
      submitLabel="Đổi mật khẩu"
      canSubmit={Boolean(password)}
      onSubmit={submit}
      onClose={onClose}
    >
      <TextField
        label="Mật khẩu mới"
        type="password"
        autoComplete="new-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        autoFocus
      />
    </FormDialog>
  );
}
