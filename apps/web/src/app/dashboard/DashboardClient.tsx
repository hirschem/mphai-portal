"use client";
import { useEffect, useState } from "react";
import AuthGuard from "../../components/AuthGuard";
import LogoutButton from "../../components/LogoutButton";
import { readAuthLevel } from "../../lib/auth";
import { apiFetchWithMeta } from "../../lib/apiClient";

export default function DashboardClient() {
  const [requestId, setRequestId] = useState("");
  const [apiStatus, setApiStatus] = useState("");
  const level = readAuthLevel();

  async function pingApi() {
    type PingResponse = { status?: string };
    const res = await apiFetchWithMeta<PingResponse>("/health", { method: "GET" });
    setRequestId(res.requestId || "");
    if (!res.ok) {
      const errMsg = typeof res.error === "object" && res.error !== null && "message" in res.error
        ? String((res.error as { message?: unknown }).message ?? "Error")
        : "Error";
      setApiStatus(errMsg);
      return;
    }
    setApiStatus("OK");
  }

  useEffect(() => {
    pingApi();
  }, []);

  return (
    <AuthGuard>
      <div className="max-w-xl mx-auto mt-12 bg-white rounded-lg shadow p-8 space-y-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Dashboard</h1>
        <div className="text-gray-700 text-lg"><span className="font-semibold">Level:</span> {level}</div>
        <div className="text-gray-700"><span className="font-semibold">API status:</span> {apiStatus}</div>
        <div className="text-gray-700"><span className="font-semibold">x-request-id:</span> {requestId}</div>
        <button
          onClick={pingApi}
          className="mt-4 bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 transition-colors font-medium"
        >
          Ping API
        </button>
        <div className="mt-6">
          <LogoutButton />
        </div>
      </div>
    </AuthGuard>
  );
}
