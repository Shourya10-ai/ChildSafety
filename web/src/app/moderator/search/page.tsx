'use client';

import React, { useState, useEffect } from 'react';
import TopBar from '@/components/layout/TopBar';
import { RiskBadge, StatusBadge } from '@/components/shared/Badges';
import { casesApi } from '@/lib/api';
import { formatDate, timeAgo, getIncidentLabel } from '@/lib/utils';
import { Search, Filter, SlidersHorizontal, ArrowUpDown } from 'lucide-react';
import Link from 'next/link';

export default function CaseSearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [riskFilter, setRiskFilter] = useState<string>('all');
  const [sortField, setSortField] = useState<'updatedAt' | 'riskLevel' | 'incidentCount'>('updatedAt');
  const [casesList, setCasesList] = useState<any[]>([]);

  useEffect(() => {
    casesApi.getCases().then((list) => {
      if (list && list.length > 0) {
        setCasesList(list);
      }
    }).catch(() => {});
  }, []);

  const riskOrder: Record<string, number> = { critical: 4, high: 3, medium: 2, low: 1 };

  const allCases = casesList.map((c: any) => ({
    id: c.protected_case_id || c.id,
    rawId: c.id,
    childId: c.child_id ? `CHILD-${c.child_id.slice(0, 6)}` : '#C8291',
    status: c.status || 'open',
    riskLevel: (c.risk_level || c.priority || 'high').toLowerCase(),
    description: c.description || c.title || 'Case auto-generated from incoming child safety report.',
    incidentCount: c.incidents?.length || 1,
    createdAt: c.created_at || new Date().toISOString(),
    updatedAt: c.updated_at || new Date().toISOString(),
    tags: ['grooming', 'coercion'],
  }));

  const filtered = allCases
    .filter((c) => {
      const matchSearch = searchQuery === '' ||
        c.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.childId.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.description.toLowerCase().includes(searchQuery.toLowerCase());
      const matchStatus = statusFilter === 'all' || c.status === statusFilter;
      const matchRisk = riskFilter === 'all' || c.riskLevel === riskFilter;
      return matchSearch && matchStatus && matchRisk;
    })
    .sort((a, b) => {
      if (sortField === 'updatedAt') return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
      if (sortField === 'riskLevel') return (riskOrder[b.riskLevel] || 1) - (riskOrder[a.riskLevel] || 1);
      return b.incidentCount - a.incidentCount;
    });

  return (
    <div className="min-h-screen bg-dots-pattern">
      <TopBar title="Case Search" subtitle="Search and filter across all assigned cases" />

      <div className="p-6 space-y-6">
        {/* Search + Filters */}
        <div className="glass-card p-5">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[280px]">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by Case ID, Child ID, or description..."
                className="input-field pl-9"
              />
            </div>

            <div className="flex items-center gap-2">
              <SlidersHorizontal size={14} className="text-slate-500" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="input-field !w-auto !py-2 text-xs"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="under_review">Under Review</option>
                <option value="escalated">Escalated</option>
                <option value="resolved">Resolved</option>
                <option value="closed">Closed</option>
              </select>
              <select
                value={riskFilter}
                onChange={(e) => setRiskFilter(e.target.value)}
                className="input-field !w-auto !py-2 text-xs"
              >
                <option value="all">All Risk</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
              <select
                value={sortField}
                onChange={(e) => setSortField(e.target.value as typeof sortField)}
                className="input-field !w-auto !py-2 text-xs"
              >
                <option value="updatedAt">Most Recent</option>
                <option value="riskLevel">Highest Risk</option>
                <option value="incidentCount">Most Incidents</option>
              </select>
            </div>
          </div>
          <p className="text-[11px] text-slate-500 mt-3">{filtered.length} cases found</p>
        </div>

        {/* Results Table */}
        <div className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="text-left px-5 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Case</th>
                  <th className="text-left px-5 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Child</th>
                  <th className="text-left px-5 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                  <th className="text-left px-5 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Risk</th>
                  <th className="text-left px-5 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Incidents</th>
                  <th className="text-left px-5 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Tags</th>
                  <th className="text-left px-5 py-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Updated</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((c, idx) => (
                  <tr
                    key={c.id}
                    className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-all cursor-pointer animate-fade-in group"
                    style={{ animationDelay: `${idx * 0.03}s` }}
                  >
                    <td className="px-5 py-4">
                      <Link href={`/moderator/cases/${c.id}`} className="text-sm font-semibold text-cyan-400 hover:text-cyan-300 group-hover:underline">
                        {c.id}
                      </Link>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-sm text-white font-medium">{c.childId}</span>
                    </td>
                    <td className="px-5 py-4"><StatusBadge status={c.status} /></td>
                    <td className="px-5 py-4"><RiskBadge level={c.riskLevel} /></td>
                    <td className="px-5 py-4">
                      <span className="text-sm font-semibold text-white">{c.incidentCount}</span>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex flex-wrap gap-1">
                        {c.tags.map((tag: string) => (
                          <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-slate-400 capitalize">
                            {getIncidentLabel(tag as any)}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-xs text-slate-400">{timeAgo(c.updatedAt)}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-16">
            <Search size={40} className="text-slate-700 mx-auto mb-3" />
            <p className="text-sm text-slate-500">No cases match your search criteria</p>
          </div>
        )}
      </div>
    </div>
  );
}
