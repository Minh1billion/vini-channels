import { useState } from 'react';
import type { ChannelRecord } from '@/entities/channel/types';
import { providersApi } from '@/shared/api';
import { FormDialog, TextField } from '@/shared/ui';

interface Props {
  channel: ChannelRecord;
  onClose: () => void;
  onSaved: () => void;
}

export function ChannelTokenDialog({ channel, onClose, onSaved }: Props) {
  const [accessToken, setAccessToken] = useState('');
  const [refreshToken, setRefreshToken] = useState('');
  const [expiresAt, setExpiresAt] = useState('');

  const expiry = expiresAt ? new Date(expiresAt) : null;
  const valid = accessToken.trim() !== '' && expiry !== null && !Number.isNaN(expiry.getTime());

  const submit = async () => {
    if (!expiry) return;
    await providersApi.setChannelToken(channel.id, {
      access_token: accessToken.trim(),
      refresh_token: refreshToken.trim() || null,
      expires_at: expiry.toISOString(),
    });
    onSaved();
  };

  return (
    <FormDialog
      title="Token TikTok"
      description={`@${channel.handle}`}
      submitLabel="Lưu token"
      canSubmit={valid}
      onSubmit={submit}
      onClose={onClose}
    >
      <TextField
        label="Access token"
        type="password"
        autoComplete="off"
        value={accessToken}
        onChange={(e) => setAccessToken(e.target.value)}
        autoFocus
        required
      />
      <TextField
        label="Refresh token (không bắt buộc)"
        type="password"
        autoComplete="off"
        value={refreshToken}
        onChange={(e) => setRefreshToken(e.target.value)}
      />
      <TextField
        label="Hết hạn lúc"
        type="datetime-local"
        value={expiresAt}
        onChange={(e) => setExpiresAt(e.target.value)}
        required
      />
    </FormDialog>
  );
}
