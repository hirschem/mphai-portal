'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

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
    // Check localStorage for existing auth (no password)
    const stored = localStorage.getItem('mph_auth')
    if (stored) {
      try {
        const { authLevel } = JSON.parse(stored)
        setAuthLevel(authLevel)
        setPassword(null)
      } catch (e) {
        localStorage.removeItem('mph_auth')
      }
    }
  }, [])

  const login = async (pwd: string) => {
    const { apiFetch } = await import("@/lib/apiClient");
    const response = await apiFetch("/api/auth/login", {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: pwd }),
    });

    if (!response.ok) {
      throw new Error('Invalid password')
    }

    const data = await response.json()
    setAuthLevel(data.level)
    setPassword(pwd)
    localStorage.setItem('mph_auth', JSON.stringify({ authLevel: data.level }))
  }

  const logout = () => {
    setAuthLevel(null)
    setPassword(null)
    localStorage.removeItem('mph_auth')
  }

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
