"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiFetchWithMeta } from "@/lib/apiClient";
import { useAuth } from "@/contexts/AuthContext";

interface Proposal {
  session_id: string;
  client_name?: string;
  project_address?: string;
  total?: number;
  created_at: string;
  has_pdf: boolean;
}

type ProposalListResponse = { proposals?: Proposal[] };

export default function InvoiceHistoryPage() {
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const { isAdmin } = useAuth();
  const router = useRouter();

  const loadProposals = useCallback(async () => {
    try {
      setLoading(true);

      const res = await apiFetchWithMeta<ProposalListResponse>("/api/history/list");
      if (!res.ok) throw res.error ?? new Error("Failed to load proposals");
      if (!res.data) throw new Error("Failed to load proposals");

      setProposals(res.data.proposals ?? []);
    } catch (err) {
      setError("Failed to load proposals");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAdmin) {
      router.push("/");
      return;
    }
    void loadProposals();
  }, [isAdmin, router, loadProposals]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-700 mx-auto mb-4" />
          <p className="text-gray-600">Loading proposals...</p>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <header className="mb-8">
          <Link
            href="/invoice"
            className="text-blue-600 hover:text-blue-700 text-sm mb-2 inline-block"
          >
            ← Back to Invoice Mode
          </Link>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">Invoice History</h1>
          <p className="text-gray-600">View and manage saved invoices</p>
        </header>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {proposals.length === 0 ? (
          <div className="bg-white rounded-xl shadow-lg p-12 text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">No invoices yet</h2>
            <p className="text-gray-600 mb-6">Create your first invoice to see it here.</p>
            <Link
              href="/invoice"
              className="inline-block bg-gray-800 text-white px-6 py-3 rounded-lg hover:bg-gray-900 transition-colors"
            >
              Create Invoice
            </Link>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {proposals.map((p: Proposal, idx: number) => (
              <div
                key={p?.session_id ?? idx}
                className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow"
              >
                <div className="mb-2 font-semibold text-gray-900">
                  {p?.client_name ?? p?.project_address ?? "Invoice"}
                </div>
                <div className="text-sm text-gray-600">
                  {p?.created_at ? new Date(p.created_at).toLocaleDateString() : ""}
                </div>

                {/* Swap this section with your existing buttons/actions */}
                <div className="mt-4">
                  <Link
                    href="/invoice"
                    className="text-blue-600 hover:text-blue-700 text-sm"
                  >
                    Open
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
