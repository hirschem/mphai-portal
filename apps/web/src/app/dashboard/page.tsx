// src/app/dashboard/page.tsx
import { Suspense } from 'react';
import DashboardClient from './DashboardClient';

export default function DashboardPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <DashboardClient />
    </Suspense>
  );
}
