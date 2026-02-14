"use client";

import { useEffect, useState, type ReactNode } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";

export default function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { authLevel } = useAuth();
  const [checking, setChecking] = useState(true);

  // Derive isAuthed from authLevel
  const isAuthed = !!authLevel;

  useEffect(() => {
    try {
      // Allow login route
      if (pathname === "/login") return;

      if (!isAuthed) {
        const next = pathname + (searchParams?.toString() ? `?${searchParams.toString()}` : "");
        router.replace(`/login?next=${encodeURIComponent(next)}`);
        return;
      }
    } finally {
      setChecking(false);
    }
  }, [isAuthed, router, pathname, searchParams]);

  if (checking) return null;
  return <>{children}</>;
}
