"use client";
// ...existing code...

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import UploadForm from '@/components/UploadForm'
import ProposalDisplay from '@/components/ProposalDisplay'
import { apiFetch, apiFetchOptional } from '@/lib/apiClient'
import { useAuth } from '@/contexts/AuthContext'

export default function InvoicePage() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [proposalData, setProposalData] = useState<unknown>(null)
  const { isAdmin, logout } = useAuth()

  // Hydrate from admin persistence on mount (admin only)
  useEffect(() => {
    if (!isAdmin) return;
    const entityId = sessionId || 'current';
    apiFetchOptional(`/api/admin-saves/invoice/${entityId}`)
      .then(({ ok, status, data, error }) => {
        if (ok && data) {
          const saved = (data ?? {}) as { proposalData?: unknown; sessionId?: string | null };
          if (saved.proposalData) setProposalData(saved.proposalData);
          if (saved.sessionId !== undefined) setSessionId(saved.sessionId || null);
        } else if (status === 404) {
            // expected empty state: no current admin save
            return;
        }
        // 401/500/other errors: handled as before (surface as error if needed)
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAdmin, sessionId]);

  // Persist to admin-saves on upload/edit (admin only)
  const persistAdminSave = useCallback((sid: string, pdata: unknown) => {
    if (!isAdmin) return;
    apiFetch(`/api/admin-saves/invoice/${sid || 'current'}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ proposalData: pdata, sessionId: sid }),
    });
  }, [isAdmin]);

  // Dev-only admin save key hint
  const devSaveKey = process.env.NODE_ENV !== 'production' && isAdmin
    ? `invoice/${sessionId || 'current'}`
    : null

  return (
    <main className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {devSaveKey && (
          <div style={{ fontSize: 12, color: '#888', marginBottom: 8, userSelect: 'all' }}>
            <span style={{ background: '#f3f3f3', padding: '2px 6px', borderRadius: 4 }}>
              [dev] admin save key: {devSaveKey}
            </span>
          </div>
        )}
        <header className="mb-8">
          <div className="flex justify-between items-center">
            <div>
              <Link 
                href="/"
                className="text-blue-600 hover:text-blue-700 text-sm mb-2 inline-block"
              >
                ← Back to Mode Selection
              </Link>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                Invoice Mode
              </h1>
              <p className="text-gray-600">
                Transform handwritten proposals into professional invoices
              </p>
            </div>
            <div className="flex gap-3">
              {isAdmin && (
                <Link
                  href="/invoice/history"
                  className="bg-gray-700 text-white px-4 py-2 rounded-lg
                    hover:bg-gray-800 transition-colors flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  View History
                </Link>
              )}
              <button
                onClick={logout}
                className="bg-red-600 text-white px-4 py-2 rounded-lg
                  hover:bg-red-700 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </header>

        <UploadForm 
          onSuccess={(sessionId, data) => {
            setSessionId(sessionId);
            setProposalData(data);
            persistAdminSave(sessionId, data);
          }}
        />

        {Boolean(proposalData) && Boolean(sessionId) && (
          <ProposalDisplay 
            data={proposalData} 
            sessionId={sessionId!}
          />
        )}
      </div>
    </main>
  )
}
