'use client';

import React, { useEffect, useState } from 'react';
import TopBar from '@/components/layout/TopBar';
import StatCard from '@/components/shared/StatCard';
import { RiskBadge, StatusBadge } from '@/components/shared/Badges';
import { timeAgo, getFlagLabel } from '@/lib/utils';
import { casesApi, sosApi, incidentsApi, reportsApi, childrenApi, SosApiRecord } from '@/lib/api';
import { realtimeService } from '@/lib/websocket';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import {
  AlertTriangle, Users, Flag, ShieldAlert, CheckCircle,
  ArrowUpRight, Brain, TrendingUp, Activity, Siren
} from 'lucide-react';
import Link from 'next/link';

export default function ModeratorDashboard() {
  const [liveSosAlerts, setLiveSosAlerts] = useState<SosApiRecord[]>([]);
  const [apiCases, setApiCases] = useState<any[]>([]);
  const [apiIncidents, setApiIncidents] = useState<any[]>([]);
  const [apiReports, setApiReports] = useState<any[]>([]);
  const [assignedChildrenCount, setAssignedChildrenCount] = useState<number>(0);

  useEffect(() => {
    casesApi.checkSla().catch(() => {});

    const loadLiveData = async () => {
      try {
        const [activeSos, casesRes, incidentsRes, reportsRes, childrenRes] = await Promise.all([
          sosApi.getActive(10).catch(() => []),
          casesApi.getCases().catch(() => []),
          incidentsApi.getActive(10).catch(() => []),
          reportsApi.getReports(10).catch(() => []),
          childrenApi.listChildren({ limit: 200 }).catch(() => []),
        ]);
        if (activeSos) setLiveSosAlerts(activeSos);
        if (casesRes) setApiCases(casesRes);
        if (incidentsRes) setApiIncidents(incidentsRes);
        if (reportsRes) setApiReports(reportsRes);
        if (childrenRes) {
          const list = Array.isArray(childrenRes) ? childrenRes : (childrenRes.items || []);
          setAssignedChildrenCount(list.length);
        }
      } catch (err) {}
    };
    loadLiveData();

    realtimeService.connect();
    const unsubscribe = realtimeService.subscribe((event, data) => {
      if (event === 'SOS_TRIGGERED' || event === 'SOS_ALERT') {
        const newSos: SosApiRecord = data.id ? data : {
          id: `sos-${Date.now()}`,
          latitude: data.latitude || 28.6139,
          longitude: data.longitude || 77.2090,
          location_address: data.location_address || 'New Delhi, India',
          status: 'ACTIVE',
          message: data.message || 'Emergency SOS triggered',
          is_silent_duress: !!data.is_silent_duress,
          created_at: new Date().toISOString(),
        };
        setLiveSosAlerts((prev) => [newSos, ...prev]);
      } else if (event === 'CASE_STATUS_CHANGED' || event === 'NEW_REPORT') {
        loadLiveData();
      }
    });

    return () => unsubscribe();
  }, []);

  const activeCasesCount = apiCases.filter(c => c.status !== 'closed' && c.status !== 'resolved').length;
  const urgentCasesCount = apiCases.filter(c => c.risk_level === 'CRITICAL' || c.priority === 'high').length;
  const resolvedCasesCount = apiCases.filter(c => c.status === 'resolved' || c.status === 'closed').length;

  const stats = {
    activeCases: activeCasesCount,
    activeCasesDelta: 0,
    newFlags: apiIncidents.length + apiReports.length,
    newFlagsDelta: 0,
    urgentCases: urgentCasesCount,
    urgentCasesDelta: urgentCasesCount > 0 ? 1 : 0,
    assignedChildren: assignedChildrenCount,
    assignedChildrenDelta: 0,
    resolvedThisWeek: resolvedCasesCount,
    resolvedDelta: 0,
  };

  const pendingFlags = [...apiIncidents, ...apiReports];
  const recentCases = apiCases.slice(0, 5);

  // Build live trend from cases grouped by day of week
  const DAYS_ORDER = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const dayMap: Record<string, { date: string; incidents: number; riskScore: number }> = {};
  const nowDate = new Date();
  for (let i = 6; i >= 0; i--) {
    const d = new Date(nowDate);
    d.setDate(nowDate.getDate() - i);
    const label = DAYS_ORDER[d.getDay()];
    dayMap[label] = { date: label, incidents: 0, riskScore: 0 };
  }
  apiCases.forEach((c: any) => {
    if (!c.created_at) return;
    const label = DAYS_ORDER[new Date(c.created_at).getDay()];
    if (label in dayMap) {
      dayMap[label].incidents += 1;
      dayMap[label].riskScore = Math.min(1, dayMap[label].riskScore + 0.15);
    }
  });
  apiIncidents.forEach((inc: any) => {
    if (!inc.created_at) return;
    const label = DAYS_ORDER[new Date(inc.created_at).getDay()];
    if (label in dayMap) dayMap[label].incidents += 1;
  });
  const chartData = Object.values(dayMap);

  return (
    <div className="min-h-screen bg-slate-950">
      <TopBar title="Moderator Portal" subtitle="Child welfare management & active safety stream" />

      <div className="p-4 sm:p-6 space-y-4 sm:space-y-6 stagger-children">
        {/* Real-time SOS Alert Banner */}
        {liveSosAlerts.map((sos) => (
          <div
            key={sos.id}
            className={`p-4 rounded-2xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 ${
              sos.is_silent_duress
                ? 'bg-rose-500/15 border-rose-500/40 shadow-lg shadow-rose-500/10'
                : 'bg-amber-500/15 border-amber-500/40 shadow-lg shadow-amber-500/10'
            }`}
          >
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${sos.is_silent_duress ? 'bg-rose-500/30 text-rose-300' : 'bg-amber-500/30 text-amber-300'}`}>
                <Siren size={20} className={sos.is_silent_duress ? 'animate-bounce' : ''} />
              </div>
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[10px] font-extrabold uppercase px-2 py-0.5 rounded bg-rose-600 text-white">
                    {sos.is_silent_duress ? 'CRITICAL SILENT DURESS' : 'ACTIVE EMERGENCY SOS'}
                  </span>
                  <span className="text-xs text-slate-300 font-medium">
                    {sos.is_silent_duress ? 'Domestic abuse scenario — alternate adults notified' : 'Standard Emergency Alert'}
                  </span>
                </div>
                <p className="text-xs sm:text-sm font-semibold text-white mt-1">
                  Location: {sos.location_address || `${sos.latitude}, ${sos.longitude}`} {sos.message ? `— "${sos.message}"` : ''}
                </p>
              </div>
            </div>
            <Link
              href="/authority/dashboard"
              className="w-full sm:w-auto text-center px-4 py-2 rounded-xl bg-white text-slate-900 font-semibold text-xs hover:bg-slate-200 transition-all flex items-center justify-center gap-1"
            >
              Dispatch Authority <ArrowUpRight size={14} />
            </Link>
          </div>
        ))}

        {/* Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-5 gap-3 sm:gap-4">
          <StatCard title="Active Cases" value={stats.activeCases} delta={stats.activeCasesDelta} icon={<Activity size={18} />} accentColor="#38bdf8" />
          <StatCard title="New AI Flags" value={stats.newFlags} delta={stats.newFlagsDelta} icon={<Flag size={18} />} accentColor="#a78bfa" variant="warning" />
          <StatCard title="Urgent Cases" value={stats.urgentCases} delta={stats.urgentCasesDelta} icon={<AlertTriangle size={18} />} accentColor="#f87171" variant="danger" />
          <StatCard title="Assigned Children" value={stats.assignedChildren} delta={stats.assignedChildrenDelta} icon={<Users size={18} />} accentColor="#34d399" />
          <StatCard title="Resolved (Week)" value={stats.resolvedThisWeek} delta={stats.resolvedDelta} icon={<CheckCircle size={18} />} accentColor="#34d399" variant="success" />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
          {/* Risk Trend Chart */}
          <div className="lg:col-span-2 glass-card p-4 sm:p-6 bg-slate-900 border border-slate-800 rounded-2xl">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xs sm:text-sm font-bold text-white flex items-center gap-2">
                  <TrendingUp size={16} className="text-blue-400" />
                  Risk Trend Analytics
                </h3>
                <p className="text-[11px] text-slate-400 mt-0.5">Aggregated risk score trajectory across children</p>
              </div>
            </div>
            <div className="w-full h-48 sm:h-56">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="riskGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#2563eb" stopOpacity={0.4} />
                      <stop offset="100%" stopColor="#2563eb" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '10px', fontSize: '12px' }}
                  />
                  <Area type="monotone" dataKey="riskScore" stroke="#3b82f6" strokeWidth={2} fill="url(#riskGradient)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Incident Distribution */}
          <div className="glass-card p-4 sm:p-6 bg-slate-900 border border-slate-800 rounded-2xl">
            <h3 className="text-xs sm:text-sm font-bold text-white flex items-center gap-2 mb-4">
              <Activity size={16} className="text-violet-400" />
              Incident Distribution
            </h3>
            <div className="w-full h-48 sm:h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData}>
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                  <Tooltip
                    contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '10px', fontSize: '12px' }}
                  />
                  <Bar dataKey="incidents" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Bottom Row: AI Flags + Recent Cases */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          {/* Pending AI Flags */}
          <div className="glass-card p-4 sm:p-6 bg-slate-900 border border-slate-800 rounded-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs sm:text-sm font-bold text-white flex items-center gap-2">
                <Brain size={16} className="text-violet-400" />
                Pending AI Flags
              </h3>
              <Link href="/moderator/flags" className="text-[11px] text-blue-400 hover:underline font-semibold flex items-center gap-1">
                View all <ArrowUpRight size={12} />
              </Link>
            </div>
            <div className="space-y-2">
              {pendingFlags.slice(0, 4).map((flag) => (
                <div key={flag.id} className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center flex-shrink-0">
                      <Flag size={14} className="text-violet-400" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-white truncate">{flag.childId}</span>
                        <RiskBadge level={flag.riskLevel} />
                      </div>
                      <p className="text-[11px] text-slate-400 truncate">{getFlagLabel(flag.type)} · {Math.round(flag.confidence * 100)}%</p>
                    </div>
                  </div>
                  <span className="text-[10px] text-slate-500 ml-2 flex-shrink-0">{timeAgo(flag.detectedAt)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Cases */}
          <div className="glass-card p-4 sm:p-6 bg-slate-900 border border-slate-800 rounded-2xl">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs sm:text-sm font-bold text-white flex items-center gap-2">
                <ShieldAlert size={16} className="text-blue-400" />
                Recent Active Cases
              </h3>
              <Link href="/moderator/search" className="text-[11px] text-blue-400 hover:underline font-semibold flex items-center gap-1">
                Search all <ArrowUpRight size={12} />
              </Link>
            </div>
            <div className="space-y-2">
              {recentCases.map((c: any) => (
                <Link key={c.id} href={`/moderator/cases/${c.id}`}>
                  <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:bg-slate-800/50 transition-all">
                    <div className="min-w-0 flex-1 pr-2">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-xs font-bold text-white">{c.id}</span>
                        <StatusBadge status={(c.status || 'active').toLowerCase() as any} />
                      </div>
                      <p className="text-[11px] text-slate-400 truncate">{c.description || c.title}</p>
                    </div>
                    <RiskBadge level={(c.riskLevel || c.priority || 'medium').toLowerCase() as any} />
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
