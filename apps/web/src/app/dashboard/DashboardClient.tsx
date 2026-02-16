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
    const res = await apiFetchWithMeta<PingResponse>("/", { method: "GET" });
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
      <div>
        <h1>Dashboard</h1>
        <div>Level: {level}</div>
        <div>API status: {apiStatus}</div>
        <div>x-request-id: {requestId}</div>
        <button onClick={pingApi}>Ping API</button>
        <LogoutButton />
      </div>
    </AuthGuard>
  );
}
