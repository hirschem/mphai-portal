'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { readAuthToken, writeAuthToken, clearAuthToken, readAuthLevel, writeAuthLevel, clearAuthLevel } from '../lib/auth';
import { apiFetch } from '@/lib/apiClient';

export type AuthLevel = 'demo' | 'admin' | null

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
    // If something "auto-logged in" by setting level only, kill it.
    if (!token && level) {
      clearAuthLevel();
    }
    setPassword(token);
    setAuthLevel(token ? level : null);
  }, []);

  const login = async (pwd: string) => {
    // Debug: log when login() is called
    console.debug('[AuthContext] login() called', { pwd });
    type LoginResponse = { access_token?: string; level?: string };
    const data = await apiFetch<LoginResponse>("/api/auth/login", {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: pwd }),
    });
    const token = typeof data.access_token === 'string' && data.access_token.length > 0 ? data.access_token : null;
    const level = data.level === 'admin' || data.level === 'demo' ? data.level : 'admin';
    if (!token) throw new Error('No access token returned');
    setAuthLevel(level);
    setPassword(token);
    writeAuthToken(token);
    console.log("WRITE DEBUG", localStorage.getItem("auth_token"));
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
        isAuthenticated: !!password,
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
