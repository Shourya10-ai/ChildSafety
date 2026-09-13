'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore, useUIStore } from '@/lib/store';
import Sidebar from '@/components/layout/Sidebar';
import MobileNav from '@/components/layout/MobileNav';

export default function ModeratorLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();
  const { sidebarCollapsed } = useUIStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && (!isAuthenticated || !user)) {
      router.replace('/login');
    }
  }, [mounted, isAuthenticated, user, router]);

  if (!mounted || !isAuthenticated || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <MobileNav />
      <Sidebar />
      <main
        className="transition-all duration-300 min-h-screen pb-20 md:pb-0"
        style={{
          marginLeft: typeof window !== 'undefined' && window.innerWidth < 768 ? 0 : (sidebarCollapsed ? 72 : 280),
        }}
      >
        {children}
      </main>
    </div>
  );
}
