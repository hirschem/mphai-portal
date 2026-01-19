'use client'

import { useState, useEffect } from 'react'
import { listProposals, deleteProposal } from '@/lib/api'
import Link from 'next/link'

interface Proposal {
  session_id: string
  client_name?: string
  project_address?: string
  total?: number
  created_at: string
  has_pdf: boolean
}

export default function HistoryPage() {
  const [proposals, setProposals] = useState<Proposal[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadProposals()
  }, [])

  const loadProposals = async () => {
    try {
      setLoading(true)
      const data = await listProposals()
      setProposals(data.proposals)
    } catch (err: any) {
      setError(err.message || 'Failed to load proposals')
    } finally {
      setLoading(false)
    }
  }
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (sessionId: string) => {
    if (!confirm('Are you sure you want to delete this proposal?')) {
      return
    }

    try {
      await deleteProposal(sessionId)
      setProposals(proposals.filter(p => p.session_id !== sessionId))
    } catch (err: any) {
      alert('Failed to delete proposal')
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    })
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <Link 
              href="/"
              className="text-blue-600 hover:text-blue-700 text-sm mb-2 inline-block"
            >
              ← Back to Mode Selection
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">
              Invoice History
            </h1>
          </div>
          <Link
            href="/invoice"
            className="bg-blue-600 text-white px-4 py-2 rounded-lg
              hover:bg-blue-700 transition-colors"
          >
            + New Invoice
          </Link>
        </div>

        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading proposals...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {!loading && !error && proposals.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="mt-2 text-lg font-medium text-gray-900">No proposals yet</h3>
            <p className="mt-1 text-gray-500">Get started by creating your first proposal.</p>
            <Link
              href="/"
              className="mt-6 inline-block bg-blue-600 text-white px-6 py-3 rounded-lg
                hover:bg-blue-700 transition-colors font-medium"
            >
              Create Proposal
            </Link>
          </div>
        )}

        {!loading && !error && proposals.length > 0 && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {proposals.map((proposal) => (
              <div
                key={proposal.session_id}
                className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg text-gray-900 mb-1">
                      {proposal.client_name || 'Unnamed Client'}
                    </h3>
                    <p className="text-sm text-gray-600 mb-2">
                      {proposal.project_address || 'No address provided'}
                    </p>
                    <p className="text-xs text-gray-500">
                      {formatDate(proposal.created_at)}
                    </p>
                  </div>
                  <button
                    onClick={() => handleDelete(proposal.session_id)}
                    className="text-red-600 hover:text-red-800 p-1"
                    title="Delete proposal"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>

                {proposal.total && (
                  <div className="mb-4">
                    <span className="text-2xl font-bold text-green-600">
                      ${proposal.total.toFixed(2)}
                    </span>
                  </div>
                )}

                <div className="flex gap-2">
                  <Link
                    href={`/proposal/${proposal.session_id}`}
                    className="flex-1 bg-blue-600 text-white text-center py-2 px-4 rounded-lg
                      hover:bg-blue-700 transition-colors text-sm font-medium"
                  >
                    View Details
                  </Link>
                  {proposal.has_pdf && (
                    <a
                      href={`${process.env.NEXT_PUBLIC_API_URL}/api/proposals/download/${proposal.session_id}`}
                      download
                      className="bg-green-600 text-white py-2 px-4 rounded-lg
                        hover:bg-green-700 transition-colors text-sm font-medium"
                      title="Download PDF"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                          d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
