// src/components/LogoutButton.tsx
'use client';
import { useRouter } from 'next/navigation';
import { clearAuthToken } from '../lib/auth';

export default function LogoutButton() {
  const router = useRouter();
  return (
    <button
      onClick={() => {
        clearAuthToken();
        router.replace('/login');
      }}
    >
      Logout
    </button>
  );
}
