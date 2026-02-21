"use client";
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { writeAuthToken, writeAuthLevel, readAuthToken } from '../../lib/auth';
import { apiFetch } from '../../lib/apiClient';

export default function LoginPage() {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  // On mount, if already authed, redirect
  useEffect(() => {
    const token = readAuthToken();
    if (token) {
      const params = new URLSearchParams(window.location.search);
      const next = params.get('next') || '/dashboard';
      router.replace(next);
    }
  }, [router]);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      type LoginResponse = { access_token: string; level?: string };
      const data = await apiFetch<LoginResponse>('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ password }),
      });
      writeAuthToken(data.access_token);
      const level = data.level === 'admin' || data.level === 'demo' ? data.level : 'admin';
      writeAuthLevel(level);
      const params = new URLSearchParams(window.location.search);
      const next = params.get('next') || '/dashboard';
      router.replace(next);
    } catch (err: unknown) {
      const maybeError = err as { status?: number; message?: string };
      if (typeof maybeError.status === 'number' && maybeError.status === 401) setError('Invalid password');
      else if (typeof maybeError.message === 'string') setError(maybeError.message || 'Unexpected error');
      else setError('Unexpected error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleLogin}>
      <input
        type="password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        placeholder="Password"
        autoFocus
        required
      />
      <button type="submit" disabled={loading}>{loading ? 'Logging in...' : 'Login'}</button>
      {error && <div style={{ color: 'red' }}>{error}</div>}
    </form>
  );
}
