
'use client'

import LoginPage from '@/components/LoginPage'
import ModeSelector from '@/components/ModeSelector'
import { useAuth } from '@/contexts/AuthContext'
import { apiHealth, apiAuthProbe } from '@/lib/apiClient';

if (typeof window !== "undefined") {
  (window as any).apiHealth = apiHealth;
  (window as any).apiAuthProbe = apiAuthProbe;
}

export default function Home() {
  const { isAuthenticated, logout } = useAuth()

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return (
    <div className="relative">
      <button
        onClick={logout}
        className="absolute top-4 right-4 bg-red-600 text-white px-4 py-2 rounded-lg
          hover:bg-red-700 transition-colors z-10"
      >
        Logout
      </button>
      <ModeSelector />
    </div>
  )
}
