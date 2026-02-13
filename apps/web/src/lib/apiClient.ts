export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
// TEMP DEBUG
console.log("API_URL runtime:", API_URL);

export function getStoredAuth() {
  const stored = localStorage.getItem('mph_auth');
  if (stored) {
    try {
      const { password, authLevel } = JSON.parse(stored);
      return { password, authLevel };
    } catch (e) {
      return null;
    }
  }
  return null;
}

export function authHeaders() {
  console.log("Stored auth:", localStorage.getItem("mph_auth"));
  const auth = getStoredAuth();
  if (auth && auth.password) {
    return { Authorization: `Bearer ${auth.password}` };
  }
  return {};
}

export async function apiFetch(path, options = {}) {
  const url = `${API_URL}${path}`;
  const finalHeaders = {
    ...(options.headers || {}),
    ...authHeaders(),
  };
  console.log("Outgoing headers:", finalHeaders);
  return fetch(url, { ...options, headers: finalHeaders });
}