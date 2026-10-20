import { useState } from 'react';
import { roleLabels } from '@/entities/user/model';
import type { Role } from '@/entities/user/types';
import { usersApi } from '@/shared/api';
import { FormDialog, SelectField, TextField } from '@/shared/ui';

const ROLES: Role[] = ['admin', 'manager', 'analyst', 'viewer'];

interface Props {
  onClose: () => void;
  onSaved: () => void;
}

export function UserDialog({ onClose, onSaved }: Props) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<Role>('viewer');

  const submit = async () => {
    await usersApi.create({ email: email.trim(), password, role });
    onSaved();
  };

  return (
    <FormDialog
      title="Thêm người dùng"
      size="sm"
      submitLabel="Tạo người dùng"
      pendingLabel="Đang tạo..."
      canSubmit={Boolean(email.trim() && password)}
      onSubmit={submit}
      onClose={onClose}
    >
      <TextField label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
      <TextField
        label="Mật khẩu"
        type="password"
        autoComplete="new-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <SelectField label="Vai trò" value={role} onChange={(e) => setRole(e.target.value as Role)}>
        {ROLES.map((item) => (
          <option key={item} value={item}>
            {roleLabels[item]}
          </option>
        ))}
      </SelectField>
    </FormDialog>
  );
}
