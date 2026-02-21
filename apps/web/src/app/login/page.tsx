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

  // On mount, if already authed, redirect (no auto-login)
  // AUTO-LOGIN REMOVED: App now loads in logged-out state. User must log in manually.
  // Only redirect if already authed, do not call login.
  // useEffect(() => {
  //   const token = readAuthToken();
  //   if (token) {
  //     const params = new URLSearchParams(window.location.search);
  //     const next = params.get('next') || '/dashboard';
  //     router.replace(next);
  //   }
  // }, [router]);

  // Use AuthContext for login
  import { useAuth } from '../../contexts/AuthContext';
  const { login } = useAuth();
  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(password);
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
