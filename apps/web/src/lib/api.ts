// src/lib/api.ts

export async function listProposals() {
	const { apiFetch } = await import("@/lib/apiClient");
	return apiFetch("/api/history/list");
}

export async function getProposal(sessionId: string) {
	const { apiFetch } = await import("@/lib/apiClient");
	return apiFetch(`/api/history/${sessionId}`);
}

export async function deleteProposal(sessionId: string) {
	const { apiFetch } = await import("@/lib/apiClient");
	return apiFetch(`/api/history/${sessionId}`, {
		method: 'DELETE',
	});
}
