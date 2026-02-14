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
    const { ok, requestId, error } = await apiFetchWithMeta("/", { method: "GET" });
    setRequestId(requestId || "");
    const errMsg =
      typeof error === "object" && error !== null && "message" in error
        ? String((error as { message?: unknown }).message ?? "Error")
        : "Error";
    setApiStatus(ok ? "OK" : errMsg);
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
