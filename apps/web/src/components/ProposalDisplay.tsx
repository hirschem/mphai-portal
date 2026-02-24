'use client'

import { useAuth } from '../contexts/AuthContext';
import { apiFetchBlobWithMeta } from "@/lib/apiClient";

interface ProposalDisplayProps {
  sessionId: string | null;
  data: unknown;
  onEdit?: (data: unknown) => void;
}

export default function ProposalDisplay({ sessionId, data }: ProposalDisplayProps) {
  const { } = useAuth();

  const d = data as Record<string, unknown>;
  const proposal =
    typeof d.proposal_data === 'object' && d.proposal_data !== null
      ? (d.proposal_data as Record<string, unknown>)
      : {};

  const handleDownload = async () => {
    if (!sessionId) return;
    const { data: blob } = await apiFetchBlobWithMeta(
      `/api/proposals/download/${sessionId}`,
      { method: "GET" }
    );
    if (!blob) return;
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `MPH_Document_${sessionId}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  };

  // ...existing code...

  // Early return if no sessionId
  if (!sessionId) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Professional Proposal</h2>
        <div className="flex gap-2 mb-6">
          <button
            disabled
            className="bg-green-300 text-white px-6 py-3 rounded-lg font-medium flex items-center gap-2 opacity-50 cursor-not-allowed"
          >
            Download PDF
          </button>
        </div>
        <div className="text-gray-700">No session loaded. Please upload a proposal.</div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6 flex-wrap gap-3">
        <h2 className="text-2xl font-bold text-gray-900">Professional Proposal</h2>
        <div className="flex gap-2">
          <button
            onClick={handleDownload}
            className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors font-medium flex items-center gap-2"
            disabled={!sessionId}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            Download PDF
          </button>
        </div>
      </div>

      <div className="space-y-6">
        <section>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Client Information</h3>
          <p className="text-gray-700"><strong>Name:</strong> {(proposal.client_name as string) || 'N/A'}</p>
          <p className="text-gray-700"><strong>Address:</strong> {(proposal.project_address as string) || 'N/A'}</p>
        </section>

        <section>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">Professional Text</h3>
          <div className="bg-gray-50 p-4 rounded-md whitespace-pre-wrap">{d.professional_text as string}</div>
        </section>

        {Array.isArray(proposal.scope_of_work) && (
          <section>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">Scope of Work</h3>
            <ul className="list-disc list-inside space-y-1">
              {(proposal.scope_of_work as unknown[]).map((item, idx) => (
                <li key={idx} className="text-gray-700">{item as string}</li>
              ))}
            </ul>
          </section>
        )}

        {typeof proposal.total === 'number' && (
          <section>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">Total</h3>
            <p className="text-2xl font-bold text-green-600">${(proposal.total as number).toFixed(2)}</p>
          </section>
        )}
      </div>

      <div className="mt-8 p-4 bg-blue-50 rounded-lg">
        <p className="text-sm text-gray-700">✅ Your professional proposal has been generated and is ready to download or email to your client.</p>
      </div>
    </div>
  );
}