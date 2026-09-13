'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthStore } from '@/lib/store';
import {
  LayoutDashboard, Users, Flag, Search, MessageSquare,
  AlertTriangle, Eye, GitBranch, MapPin, Download, Menu, X, LogOut, Shield, UserCircle, Bell
} from 'lucide-react';

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  badge?: number;
}

const moderatorNav: NavItem[] = [
  { label: 'Dashboard', href: '/moderator/dashboard', icon: <LayoutDashboard size={20} /> },
  { label: 'Assigned Children', href: '/moderator/children', icon: <Users size={20} /> },
  { label: 'AI Flags', href: '/moderator/flags', icon: <Flag size={20} />, badge: 6 },
  { label: 'Case Search', href: '/moderator/search', icon: <Search size={20} /> },
  { label: 'Communication', href: '/moderator/chat', icon: <MessageSquare size={20} />, badge: 1 },
];

const authorityNav: NavItem[] = [
  { label: 'Dashboard', href: '/authority/dashboard', icon: <LayoutDashboard size={20} /> },
  { label: 'Escalated Cases', href: '/authority/cases', icon: <AlertTriangle size={20} />, badge: 4 },
  { label: 'Missing Children', href: '/authority/missing', icon: <Eye size={20} />, badge: 2 },
  { label: 'Knowledge Graph', href: '/authority/graph', icon: <GitBranch size={20} /> },
  { label: 'Geographic Intel', href: '/authority/geo', icon: <MapPin size={20} /> },
  { label: 'Case Export', href: '/authority/export', icon: <Download size={20} /> },
];

export default function MobileNav() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const [drawerOpen, setDrawerOpen] = useState(false);

  if (!user) return null;

  const navItems = user.role === 'moderator' ? moderatorNav : authorityNav;
  const portalLabel = user.role === 'moderator' ? 'Moderator Portal' : 'Authority Portal';

  // Bottom bar quick items (first 4)
  const bottomItems = navItems.slice(0, 4);

  return (
    <>
      {/* Mobile Top Header */}
      <div className="md:hidden sticky top-0 z-40 bg-slate-900/95 backdrop-blur-md border-b border-slate-800 px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white">
            <Shield size={18} />
          </div>
          <div>
            <h1 className="text-xs font-bold text-white tracking-tight leading-none">Child Safety</h1>
            <p className="text-[9px] text-blue-400 font-semibold uppercase">{portalLabel}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setDrawerOpen(!drawerOpen)}
            className="p-2 rounded-lg bg-slate-800 text-slate-300 hover:text-white"
            aria-label="Toggle mobile menu"
          >
            {drawerOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {/* Slide-over Mobile Drawer */}
      {drawerOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setDrawerOpen(false)} />
          <div className="relative w-4/5 max-w-xs bg-slate-900 border-r border-slate-800 h-full flex flex-col p-4 shadow-2xl z-10 animate-slide-in-left">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white">
                  <Shield size={20} />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-white">Child Safety</h2>
                  <p className="text-[10px] text-blue-400 font-medium uppercase">{portalLabel}</p>
                </div>
              </div>
              <button onClick={() => setDrawerOpen(false)} className="text-slate-400 hover:text-white p-1">
                <X size={20} />
              </button>
            </div>

            {/* Navigation links */}
            <nav className="flex-1 space-y-1 overflow-y-auto">
              {navItems.map((item) => {
                const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setDrawerOpen(false)}
                    className={`flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30'
                        : 'text-slate-300 hover:bg-slate-800/60'
                    }`}
                  >
                    <span className={isActive ? 'text-blue-400' : 'text-slate-400'}>{item.icon}</span>
                    <span className="flex-1">{item.label}</span>
                    {item.badge && (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
            </nav>

            {/* User profile & logout */}
            <div className="pt-4 border-t border-slate-800 space-y-3">
              <div className="flex items-center gap-3 p-2.5 rounded-xl bg-slate-800/50">
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-xs">
                  <UserCircle size={18} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-semibold text-white truncate">{user.name}</p>
                  <p className="text-[10px] text-slate-400 truncate">{user.department}</p>
                </div>
              </div>

              <button
                onClick={() => { logout(); setDrawerOpen(false); }}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 font-semibold text-xs hover:bg-rose-500/20"
              >
                <LogOut size={16} /> Sign Out
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mobile Bottom Navigation Bar */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-slate-900/95 backdrop-blur-lg border-t border-slate-800 h-16 flex items-center justify-around px-2 shadow-lg">
        {bottomItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex flex-col items-center justify-center flex-1 py-1 text-center transition-all ${
                isActive ? 'text-blue-400 font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <div className="relative">
                {item.icon}
                {item.badge && (
                  <span className="absolute -top-1 -right-2 w-3.5 h-3.5 rounded-full bg-blue-500 text-white text-[8px] font-bold flex items-center justify-center">
                    {item.badge}
                  </span>
                )}
              </div>
              <span className="text-[10px] mt-1 truncate max-w-[64px]">{item.label.split(' ')[0]}</span>
            </Link>
          );
        })}
      </div>
    </>
  );
}
