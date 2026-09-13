'use client';

import React, { useState, useEffect } from 'react';
import { Bell, Search, X, AlertTriangle, MessageSquare, Flag, Shield } from 'lucide-react';
import { useNotificationStore } from '@/lib/store';
import { notificationsApi } from '@/lib/api';
import { realtimeService } from '@/lib/websocket';
import { timeAgo } from '@/lib/utils';
import { Notification } from '@/types';

export default function TopBar({ title, subtitle }: { title: string; subtitle?: string }) {
  const [showNotifications, setShowNotifications] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const { notifications, unreadCount, setNotifications, addNotification, markAsRead, markAllAsRead } = useNotificationStore();

  // Fetch live notifications from API on mount
  useEffect(() => {
    notificationsApi.getNotifications(50).then((res) => {
      const items: Notification[] = (res?.items || []).map((n: any) => ({
        id: n.id,
        type: mapNotifType(n.notification_type),
        title: n.title,
        description: n.body || n.description || '',
        timestamp: n.created_at,
        read: n.is_read ?? false,
        priority: mapPriority(n.notification_type),
      }));
      if (items.length > 0) setNotifications(items);
    }).catch(() => {});

    // Subscribe to real-time WebSocket push notifications
    const unsub = realtimeService.subscribe((event, data) => {
      const notifMap: Record<string, { type: Notification['type']; title: string; priority: Notification['priority'] }> = {
        AI_FLAG: { type: 'ai_flag', title: 'New AI Flag Detected', priority: 'high' },
        AI_FLAGGED: { type: 'ai_flag', title: 'New AI Flag Detected', priority: 'high' },
        SOS_TRIGGERED: { type: 'sos', title: 'SOS Emergency Alert', priority: 'urgent' },
        SOS_ALERT: { type: 'sos', title: 'SOS Emergency Alert', priority: 'urgent' },
        CASE_STATUS_CHANGED: { type: 'escalation', title: 'Case Status Updated', priority: 'medium' },
        ESCALATION: { type: 'escalation', title: 'Case Escalated', priority: 'urgent' },
        NEW_REPORT: { type: 'escalation', title: 'New Report Submitted', priority: 'medium' },
        CHAT_MESSAGE: { type: 'message', title: 'New Message', priority: 'medium' },
      };
      const mapped = notifMap[event];
      if (mapped) {
        addNotification({
          id: data.id || `notif-${Date.now()}`,
          type: mapped.type,
          title: mapped.title,
          description: data.message || data.description || data.content || '',
          timestamp: data.created_at || new Date().toISOString(),
          read: false,
          priority: mapped.priority,
        });
      }
    });

    return () => unsub();
  }, []);

  function mapNotifType(t: string): Notification['type'] {
    if (t?.includes('SOS')) return 'sos';
    if (t?.includes('FLAG') || t?.includes('INCIDENT')) return 'ai_flag';
    if (t?.includes('ESCAL')) return 'escalation';
    if (t?.includes('CHAT') || t?.includes('MESSAGE')) return 'message';
    return 'escalation';
  }

  function mapPriority(t: string): Notification['priority'] {
    if (t?.includes('SOS') || t?.includes('ESCAL')) return 'urgent';
    if (t?.includes('FLAG') || t?.includes('INCIDENT')) return 'high';
    return 'medium';
  }

  const getNotifIcon = (type: string) => {
    switch (type) {
      case 'ai_flag': return <Flag size={14} className="text-violet-400" />;
      case 'sos': return <AlertTriangle size={14} className="text-rose-400" />;
      case 'escalation': return <Shield size={14} className="text-amber-400" />;
      case 'message': return <MessageSquare size={14} className="text-blue-400" />;
      default: return <Bell size={14} className="text-slate-400" />;
    }
  };

  const getPriorityDot = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-rose-500';
      case 'high': return 'bg-amber-500';
      case 'medium': return 'bg-blue-500';
      default: return 'bg-slate-500';
    }
  };

  const handleMarkAllRead = async () => {
    markAllAsRead();
    notificationsApi.markAllRead().catch(() => {});
  };

  const handleMarkRead = (id: string) => {
    markAsRead(id);
    notificationsApi.markRead(id).catch(() => {});
  };

  return (
    <header className="sticky top-0 z-30 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="flex items-center justify-between h-14 sm:h-16 px-4 sm:px-6">
        {/* Title */}
        <div className="min-w-0 flex-1">
          <h1 className="text-base sm:text-lg font-bold text-white truncate">{title}</h1>
          {subtitle && <p className="text-[11px] sm:text-xs text-slate-400 truncate mt-0.5">{subtitle}</p>}
        </div>

        {/* Right section */}
        <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0 ml-2">
          {/* Search bar */}
          <div className="relative hidden md:block">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search cases, children..."
              className="input-field pl-9 pr-4 py-1.5 w-56 lg:w-64 text-xs bg-slate-950/60 border-slate-800"
            />
          </div>

          {/* Notification bell */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 rounded-xl hover:bg-slate-800 text-slate-300 hover:text-white transition-all"
              aria-label="Notifications"
            >
              <Bell size={18} className="sm:w-5 sm:h-5" />
              {unreadCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 sm:w-5 sm:h-5 rounded-full bg-rose-500 text-white text-[9px] sm:text-[10px] font-bold flex items-center justify-center shadow-md">
                  {unreadCount}
                </span>
              )}
            </button>

            {/* Notification Dropdown */}
            {showNotifications && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setShowNotifications(false)} />
                <div className="absolute right-0 top-12 w-[90vw] max-w-sm sm:w-96 bg-slate-900 rounded-2xl shadow-2xl z-50 animate-fade-in overflow-hidden border border-slate-800">
                  <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
                    <h3 className="text-sm font-semibold text-white">Notifications</h3>
                    <div className="flex items-center gap-2">
                      {unreadCount > 0 && (
                        <button
                          onClick={handleMarkAllRead}
                          className="text-[11px] text-blue-400 hover:text-blue-300 font-medium"
                        >
                          Mark all read
                        </button>
                      )}
                      <button onClick={() => setShowNotifications(false)} className="text-slate-400 hover:text-slate-200">
                        <X size={16} />
                      </button>
                    </div>
                  </div>
                  <div className="max-h-80 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="px-4 py-8 text-center">
                        <Bell size={28} className="mx-auto text-slate-600 mb-2" />
                        <p className="text-xs text-slate-500">No notifications yet</p>
                        <p className="text-[10px] text-slate-600 mt-1">Live alerts will appear here</p>
                      </div>
                    ) : notifications.map((notif) => (
                      <div
                        key={notif.id}
                        onClick={() => handleMarkRead(notif.id)}
                        className={`flex items-start gap-3 px-4 py-3 border-b border-slate-800/60 cursor-pointer transition-all hover:bg-slate-800/50 ${
                          !notif.read ? 'bg-blue-950/20' : ''
                        }`}
                      >
                        <div className="mt-0.5 flex-shrink-0">
                          <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center">
                            {getNotifIcon(notif.type)}
                          </div>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            {!notif.read && <span className={`w-1.5 h-1.5 rounded-full ${getPriorityDot(notif.priority)}`} />}
                            <p className={`text-xs font-semibold truncate ${!notif.read ? 'text-white' : 'text-slate-300'}`}>
                              {notif.title}
                            </p>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-2">{notif.description}</p>
                          <p className="text-[10px] text-slate-500 mt-1">{timeAgo(notif.timestamp)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

