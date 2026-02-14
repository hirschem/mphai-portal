'use client'

interface ProposalDisplayProps {
  sessionId: string | null
  data: unknown
  onEdit?: (data: unknown) => void
}


export default function ProposalDisplay({ sessionId, data }: ProposalDisplayProps) {
  const d = data as Record<string, unknown>;
  const proposal = (typeof d.proposal_data === 'object' && d.proposal_data !== null)
    ? (d.proposal_data as Record<string, unknown>)
    : {};
  const clientName = (proposal.client_name as string) ?? "Client";

  const handleDownload = () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const downloadUrl = `${apiUrl}/api/proposals/download/${sessionId}`
    // Open in new tab or trigger download
    window.open(downloadUrl, '_blank')
  }

  const handleEmail = () => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const downloadUrl = `${apiUrl}/api/proposals/download/${sessionId}`
    // Create email with link to PDF
    const subject = encodeURIComponent(`Proposal for ${clientName}`)
    const body = encodeURIComponent(`Please find the proposal attached.\n\nYou can download it here: ${downloadUrl}`)
    window.location.href = `mailto:?subject=${subject}&body=${body}`
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6 flex-wrap gap-3">
        <h2 className="text-2xl font-bold text-gray-900">
          Professional Proposal
        </h2>
        <div className="flex gap-2">
          <button
            onClick={handleDownload}
            className="bg-green-600 text-white px-6 py-3 rounded-lg
              hover:bg-green-700 transition-colors font-medium flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Download PDF
          </button>
          <button
            onClick={handleEmail}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg
              hover:bg-blue-700 transition-colors font-medium flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            Email
          </button>
        </div>
      </div>

      <div className="space-y-6">
        <section>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">
            Client Information
          </h3>
          <p className="text-gray-700">
            <strong>Name:</strong> {proposal.client_name as string || 'N/A'}
          </p>
          <p className="text-gray-700">
            <strong>Address:</strong> {proposal.project_address as string || 'N/A'}
          </p>
        </section>

        <section>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">
            Professional Text
          </h3>
          <div className="bg-gray-50 p-4 rounded-md whitespace-pre-wrap">
            {d.professional_text as string}
          </div>
        </section>

        {Array.isArray(proposal.scope_of_work) && (
          <section>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              Scope of Work
            </h3>
            <ul className="list-disc list-inside space-y-1">
              {(proposal.scope_of_work as unknown[]).map((item, idx) => (
                <li key={idx} className="text-gray-700">{item as string}</li>
              ))}
            </ul>
          </section>
        )}

        {typeof proposal.total === 'number' && (
          <section>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              Total
            </h3>
            <p className="text-2xl font-bold text-green-600">
              ${(proposal.total as number).toFixed(2)}
            </p>
          </section>
        )}
      </div>

      <div className="mt-8 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-gray-700">
          ✅ Your professional proposal has been generated and is ready to download or email to your client.
        </p>
      </div>
    </div>
  )
}
