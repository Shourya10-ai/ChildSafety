'use client';

import React, { useState, useEffect } from 'react';
import TopBar from '@/components/layout/TopBar';
import { RiskBadge, RiskGauge } from '@/components/shared/Badges';
import { childrenApi, casesApi } from '@/lib/api';
import { timeAgo } from '@/lib/utils';
import { Users, TrendingUp, TrendingDown, Minus, Search, Filter, Check, X, UserPlus } from 'lucide-react';
import Link from 'next/link';

interface PendingNomination {
  id: string;
  childId: string;
  adultIdentifier: string;
  relationshipLabel: string;
  reason: string;
  status: 'PENDING_VETTING' | 'APPROVED' | 'REJECTED';
}

export default function AssignedChildrenPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [riskFilter, setRiskFilter] = useState<string>('all');
  const [childrenList, setChildrenList] = useState<any[]>([]);

  useEffect(() => {
    casesApi.getCases().then((casesRes) => {
      if (casesRes && casesRes.length > 0) {
        const mapped = casesRes.map((c: any) => ({
          id: `#C${c.child_id ? c.child_id.slice(0, 5) : '8291'}`,
          caseId: c.protected_case_id || c.id,
          age: 13,
          riskLevel: (c.risk_level || c.priority || 'high').toLowerCase(),
          riskTrend: c.priority === 'high' ? 'increasing' : 'stable',
          activeCases: 1,
          totalIncidents: c.incidents?.length || 2,
          status: c.status === 'open' ? 'active' : 'monitoring',
          lastActivity: c.updated_at || new Date().toISOString(),
        }));
        setChildrenList(mapped);
      }
    }).catch(() => {});
  }, []);

  // Pending Trusted Adult Nominations (Section 7 Rule 6)
  const [nominations, setNominations] = useState<PendingNomination[]>([
    {
      id: 'nom-101',
      childId: '#C8291',
      adultIdentifier: 'teacher.meena@school.edu.in',
      relationshipLabel: 'School Guidance Counselor',
      reason: 'Child reported feeling unsafe at home; requested outside trusted adult contact.',
      status: 'PENDING_VETTING',
    },
    {
      id: 'nom-102',
      childId: '#C4410',
      adultIdentifier: 'aunt.sunita@gmail.com',
      relationshipLabel: 'Maternal Aunt',
      reason: 'Designated alternate trusted adult for silent duress routing.',
      status: 'PENDING_VETTING',
    },
  ]);

  const handleReviewNomination = async (nomId: string, childId: string, approved: boolean) => {
    try {
      await childrenApi.reviewNomination(childId, nomId, {
        approved,
        vetting_notes: approved ? 'Vetted and verified by moderator' : 'Failed vetting check',
      });
    } catch (e) {}

    setNominations((prev) =>
      prev.map((n) => (n.id === nomId ? { ...n, status: approved ? 'APPROVED' : 'REJECTED' } : n))
    );
  };

  const filtered = childrenList.filter((child) => {
    const matchesSearch = child.id.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRisk = riskFilter === 'all' || child.riskLevel === riskFilter;
    return matchesSearch && matchesRisk;
  });

  const TrendIcon = ({ trend }: { trend: string }) => {
    if (trend === 'increasing') return <TrendingUp size={12} className="text-red-400" />;
    if (trend === 'decreasing') return <TrendingDown size={12} className="text-emerald-400" />;
    return <Minus size={12} className="text-slate-400" />;
  };

  return (
    <div className="min-h-screen bg-dots-pattern">
      <TopBar title="Assigned Children & Trusted Adults" subtitle={`${childrenList.length || 2} children under supervision · Trusted Adult Vetting Queue`} />

      <div className="p-6 space-y-6">
        {/* Trusted Adult Nomination Vetting Queue (Section 7 Rule 6) */}
        <div className="glass-card p-6 border-l-4 border-l-violet-500">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
            <UserPlus size={16} className="text-violet-400" />
            Pending Trusted Adult Vetting Queue (PUT /api/v1/children/id/nominate-adult/link_id/review)
          </h3>
          <p className="text-xs text-slate-400 mb-4">
            Nominations submitted by children enter PENDING_VETTING status. A moderator must explicitly approve or reject before they receive silent duress alerts.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {nominations.map((nom) => (
              <div key={nom.id} className="p-4 rounded-xl bg-white/[0.02] border border-white/10">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <span className="text-xs font-semibold text-cyan-400">{nom.childId}</span>
                    <span className="text-xs text-slate-300 font-medium ml-2">{nom.relationshipLabel}</span>
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    nom.status === 'PENDING_VETTING' ? 'bg-amber-500/20 text-amber-300' :
                    nom.status === 'APPROVED' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'
                  }`}>
                    {nom.status}
                  </span>
                </div>
                <p className="text-xs text-slate-200 font-mono mb-1">{nom.adultIdentifier}</p>
                <p className="text-[11px] text-slate-400 italic mb-3">&ldquo;{nom.reason}&rdquo;</p>

                {nom.status === 'PENDING_VETTING' && (
                  <div className="flex items-center gap-2 pt-2 border-t border-white/5">
                    <button
                      onClick={() => handleReviewNomination(nom.id, nom.childId, true)}
                      className="btn-primary !py-1 !px-3 !text-xs !rounded-lg"
                    >
                      <Check size={12} /> Approve & Vet
                    </button>
                    <button
                      onClick={() => handleReviewNomination(nom.id, nom.childId, false)}
                      className="btn-secondary !py-1 !px-3 !text-xs !rounded-lg"
                    >
                      <X size={12} /> Reject
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 max-w-sm">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by Child ID..."
              className="input-field pl-9"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={14} className="text-slate-500" />
            {['all', 'critical', 'high', 'medium', 'low'].map((risk) => (
              <button
                key={risk}
                onClick={() => setRiskFilter(risk)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  riskFilter === risk
                    ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/30'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent'
                }`}
              >
                {risk === 'all' ? 'All' : risk.charAt(0).toUpperCase() + risk.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Children Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 stagger-children">
          {filtered.map((child) => (
            <Link key={child.id} href={`/moderator/cases/${child.caseId}`}>
              <div className="glass-card p-5 cursor-pointer group">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 to-emerald-500/20 flex items-center justify-center">
                      <Users size={18} className="text-cyan-400" />
                    </div>
                    <div>
                      <h3 className="text-sm font-bold text-white group-hover:text-cyan-400 transition-colors">{child.id}</h3>
                      <p className="text-[11px] text-slate-500">Age: {child.age || 'N/A'}</p>
                    </div>
                  </div>
                  <RiskBadge level={child.riskLevel} />
                </div>

                {/* Risk Gauge */}
                <div className="mb-3">
                  <RiskGauge level={child.riskLevel} />
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-3 mb-3">
                  <div className="text-center p-2 rounded-lg bg-white/[0.03]">
                    <p className="text-lg font-bold text-white">{child.activeCases}</p>
                    <p className="text-[10px] text-slate-500">Active</p>
                  </div>
                  <div className="text-center p-2 rounded-lg bg-white/[0.03]">
                    <p className="text-lg font-bold text-white">{child.totalIncidents}</p>
                    <p className="text-[10px] text-slate-500">Incidents</p>
                  </div>
                  <div className="text-center p-2 rounded-lg bg-white/[0.03]">
                    <div className="flex items-center justify-center gap-1">
                      <TrendIcon trend={child.riskTrend} />
                      <p className="text-[10px] text-slate-400 capitalize">{child.riskTrend}</p>
                    </div>
                    <p className="text-[10px] text-slate-500 mt-0.5">Trend</p>
                  </div>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between pt-2 border-t border-white/5">
                  <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
                    child.status === 'active' ? 'bg-cyan-500/10 text-cyan-400' :
                    child.status === 'monitoring' ? 'bg-amber-500/10 text-amber-400' :
                    'bg-emerald-500/10 text-emerald-400'
                  }`}>
                    {child.status.charAt(0).toUpperCase() + child.status.slice(1)}
                  </span>
                  <span className="text-[10px] text-slate-600">Last active: {timeAgo(child.lastActivity)}</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
