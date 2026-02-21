"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../../contexts/AuthContext";

export default function LoginPage() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { login } = useAuth();

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(password);
      const params = new URLSearchParams(window.location.search);
      const next = params.get("next") || "/dashboard";
      router.replace(next);
    } catch (err: unknown) {
      const maybeError = err as { status?: number; message?: string };
      if (typeof maybeError.status === "number" && maybeError.status === 401) setError("Invalid password");
      else if (typeof maybeError.message === "string") setError(maybeError.message || "Unexpected error");
      else setError("Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
      <form onSubmit={handleLogin} className="w-full max-w-sm bg-white rounded-lg shadow-md p-6">
        <h1 className="text-xl font-bold text-gray-900 mb-4">Login</h1>

        <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
          Password
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          autoFocus
          required
          className="w-full border border-gray-300 rounded-md px-3 py-2 mb-3"
        />

        {error ? <div className="text-sm text-red-600 mb-3">{error}</div> : null}

        <button
          type="submit"
          disabled={loading || !password}
          className="w-full bg-blue-600 text-white rounded-md px-4 py-2 font-medium disabled:opacity-50"
        >
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>
    </main>
  );
}