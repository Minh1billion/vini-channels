import { useState } from 'react';
import { authApi } from '@/shared/api';
import { FormDialog, TextField } from '@/shared/ui';

const MIN_PASSWORD_LENGTH = 8;

interface Props {
  onClose: () => void;
  onSaved: () => void;
}

export function ChangePasswordDialog({ onClose, onSaved }: Props) {
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');

  const mismatch = confirm !== '' && confirm !== next;
  const tooShort = next !== '' && next.length < MIN_PASSWORD_LENGTH;
  const canSubmit = current !== '' && next.length >= MIN_PASSWORD_LENGTH && next === confirm;

  const submit = async () => {
    await authApi.changePassword(current, next);
    onSaved();
  };

  return (
    <FormDialog
      title="Đổi mật khẩu"
      size="sm"
      submitLabel="Đổi mật khẩu"
      canSubmit={canSubmit}
      onSubmit={submit}
      onClose={onClose}
    >
      <TextField
        label="Mật khẩu hiện tại"
        type="password"
        autoComplete="current-password"
        value={current}
        onChange={(event) => setCurrent(event.target.value)}
        required
        autoFocus
      />
      <TextField
        label="Mật khẩu mới"
        type="password"
        autoComplete="new-password"
        value={next}
        onChange={(event) => setNext(event.target.value)}
        hint={`Ít nhất ${MIN_PASSWORD_LENGTH} ký tự`}
        error={tooShort ? `Mật khẩu cần ít nhất ${MIN_PASSWORD_LENGTH} ký tự` : undefined}
        required
      />
      <TextField
        label="Nhập lại mật khẩu mới"
        type="password"
        autoComplete="new-password"
        value={confirm}
        onChange={(event) => setConfirm(event.target.value)}
        error={mismatch ? 'Mật khẩu nhập lại không khớp' : undefined}
        required
      />
    </FormDialog>
  );
}
