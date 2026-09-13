'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthStore, useUIStore } from '@/lib/store';
import {
  LayoutDashboard, Users, Shield, Flag, MessageSquare,
  Search, AlertTriangle, MapPin, GitBranch, Download,
  ChevronLeft, ChevronRight, LogOut, UserCircle, Eye
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

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();

  if (!user) return null;

  const navItems = user.role === 'moderator' ? moderatorNav : authorityNav;
  const portalLabel = user.role === 'moderator' ? 'Moderator Portal' : 'Authority Portal';

  return (
    <aside
      className={`hidden md:flex fixed top-0 left-0 h-screen z-40 flex-col transition-all duration-300 ease-in-out bg-slate-900 border-r border-slate-800 ${
        sidebarCollapsed ? 'w-[72px]' : 'w-[280px]'
      }`}
    >
      {/* Logo / Brand */}
      <div className="flex items-center gap-3 px-5 h-16 border-b border-slate-800">
        <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center flex-shrink-0 shadow-md shadow-blue-500/20">
          <Shield size={20} className="text-white" />
        </div>
        {!sidebarCollapsed && (
          <div className="animate-fade-in overflow-hidden">
            <h1 className="text-sm font-bold text-white tracking-tight leading-tight">Child Safety</h1>
            <p className="text-[10px] text-blue-400 font-semibold uppercase tracking-wider">{portalLabel}</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 relative ${
                isActive
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent'
              }`}
            >
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full bg-blue-500" />
              )}
              <span className={`flex-shrink-0 ${isActive ? 'text-blue-400' : 'text-slate-500 group-hover:text-slate-300'}`}>
                {item.icon}
              </span>
              {!sidebarCollapsed && (
                <span className="animate-fade-in truncate">{item.label}</span>
              )}
              {!sidebarCollapsed && item.badge && (
                <span className="ml-auto text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30 animate-fade-in">
                  {item.badge}
                </span>
              )}
              {sidebarCollapsed && item.badge && (
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-blue-500 text-white text-[9px] font-bold flex items-center justify-center">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* User Profile & Actions */}
      <div className="border-t border-slate-800 p-3 space-y-2">
        <div className={`flex items-center gap-3 px-3 py-2 rounded-xl bg-slate-800/50 ${sidebarCollapsed ? 'justify-center' : ''}`}>
          <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 text-white">
            <UserCircle size={18} />
          </div>
          {!sidebarCollapsed && (
            <div className="animate-fade-in overflow-hidden min-w-0">
              <p className="text-xs font-semibold text-white truncate">{user.name}</p>
              <p className="text-[10px] text-slate-400 truncate">{user.department}</p>
            </div>
          )}
        </div>

        <div className={`flex ${sidebarCollapsed ? 'flex-col' : 'flex-row'} gap-1`}>
          <button
            onClick={toggleSidebar}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all text-xs"
          >
            {sidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
            {!sidebarCollapsed && <span>Collapse</span>}
          </button>
          <button
            onClick={logout}
            className="flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-all text-xs"
          >
            <LogOut size={16} />
            {!sidebarCollapsed && <span>Logout</span>}
          </button>
        </div>
      </div>
    </aside>
  );
}
