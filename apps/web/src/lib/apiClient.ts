export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
// TEMP DEBUG
console.log("API_URL runtime:", API_URL);


// No longer reads password from localStorage. Pass password explicitly.
export function authHeaders(password?: string) {
  if (password) {
    return { Authorization: `Bearer ${password}` };
  }
  return {};
}

// apiFetch now takes optional password for auth header
export async function apiFetch(path, options = {}, password?: string) {
  const url = `${API_URL}${path}`;
  const finalHeaders = {
    ...(options.headers || {}),
    ...authHeaders(password),
  };
  return fetch(url, { ...options, headers: finalHeaders });
}