const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function uploadAndTranscribe(file: File) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_URL}/api/transcribe/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error('Failed to upload and transcribe')
  }

  return response.json()
}

export async function generateProposal(sessionId: string, rawText: string) {
  const response = await fetch(`${API_URL}/api/proposals/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      raw_text: rawText,
    }),
  })

  if (!response.ok) {
    throw new Error('Failed to generate proposal')
  }

  return response.json()
}

export async function exportProposal(sessionId: string, format: string = 'pdf') {
  const response = await fetch(`${API_URL}/api/proposals/export/${sessionId}?format=${format}`, {
    method: 'POST',
  })

  if (!response.ok) {
    throw new Error('Failed to export proposal')
  }

  return response.json()
}

function getAuthHeader(): HeadersInit {
// moved to apiClient.ts

export async function listProposals() {
  const { apiFetch } = await import("@/lib/apiClient");
  const response = await apiFetch("/api/history/list");

  if (!response.ok) {
    throw new Error('Failed to fetch proposals')
  }

  return response.json()
}

export async function getProposal(sessionId: string) {
  const { apiFetch } = await import("@/lib/apiClient");
  const response = await apiFetch(`/api/history/${sessionId}`);

  if (!response.ok) {
    throw new Error('Failed to fetch proposal')
  }

  return response.json()
}

export async function deleteProposal(sessionId: string) {
  const { apiFetch } = await import("@/lib/apiClient");
  const response = await apiFetch(`/api/history/${sessionId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete proposal')
  }

  return response.json()
}
