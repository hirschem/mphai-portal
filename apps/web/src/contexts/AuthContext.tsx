'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { readAuthToken, writeAuthToken, clearAuthToken, readAuthLevel, writeAuthLevel } from '../lib/auth';
import { apiFetch } from '@/lib/apiClient';

type AuthLevel = 'demo' | 'admin' | null

interface AuthContextType {
  authLevel: AuthLevel
  password: string | null
  login: (password: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
  isAdmin: boolean
  getAuthHeader: () => { Authorization: string }
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [authLevel, setAuthLevel] = useState<AuthLevel>(null)
  const [password, setPassword] = useState<string | null>(null)

  useEffect(() => {
    // SSR-safe: only read in browser
    const token = readAuthToken();
    const level = readAuthLevel();
    setPassword(token);
    setAuthLevel(level);
  }, []);

  const login = async (pwd: string) => {
    const { ok, data, error } = await apiFetch("/api/auth/login", {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: pwd }),
    });
    if (!ok) throw error || new Error('Invalid password');
    const authData = (data ?? {}) as { level?: string };
    const level = authData.level === 'admin' || authData.level === 'demo' ? authData.level : 'admin';
    setAuthLevel(level);
    setPassword(pwd);
    writeAuthToken(pwd);
    writeAuthLevel(level);
  };

  const logout = () => {
    setAuthLevel(null);
    setPassword(null);
    clearAuthToken();
  };

  const getAuthHeader = () => {
    if (!password) {
      throw new Error('Not authenticated')
    }
    return { Authorization: `Bearer ${password}` }
  }

  return (
    <AuthContext.Provider
      value={{
        authLevel,
        password,
        login,
        logout,
        isAuthenticated: authLevel !== null,
        isAdmin: authLevel === 'admin',
        getAuthHeader,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
