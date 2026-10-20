import { useState, type FormEvent } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/features/auth/AuthProvider';
import { ApiError } from '@/shared/api';
import { BrandMark, Button, TextField } from '@/shared/ui';

export function LoginPage() {
  const { status, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const target = (location.state as { from?: string } | null)?.from ?? '/';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (status === 'authenticated') return <Navigate to={target} replace />;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await login(email.trim(), password);
      navigate(target, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Không thể đăng nhập');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="grid min-h-screen place-items-center bg-bg px-4 text-fg">
      <form
        onSubmit={submit}
        className="flex w-full max-w-sm flex-col gap-4 rounded-card border border-border bg-card p-6"
      >
        <div className="flex items-center gap-2.5">
          <BrandMark size={32} />
          <span className="text-lg font-bold">ViniChannels</span>
        </div>
        <h1 className="text-xl font-bold">Đăng nhập</h1>
        <TextField
          label="Email"
          type="email"
          autoComplete="username"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
          autoFocus
        />
        <TextField
          label="Mật khẩu"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
        {error ? (
          <p role="alert" className="text-sm text-down">
            {error}
          </p>
        ) : null}
        <Button type="submit" variant="primary" disabled={submitting || !email || !password}>
          {submitting ? 'Đang đăng nhập...' : 'Đăng nhập'}
        </Button>
      </form>
    </main>
  );
}
