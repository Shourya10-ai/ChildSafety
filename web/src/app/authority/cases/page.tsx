'use client';

import React, { useState, useEffect } from 'react';
import TopBar from '@/components/layout/TopBar';
import { RiskBadge, StatusBadge, TrustBadge } from '@/components/shared/Badges';
import Timeline from '@/components/shared/Timeline';
import { casesApi } from '@/lib/api';
import { formatDateTime, timeAgo, getIncidentLabel } from '@/lib/utils';
import {
  AlertTriangle, Shield, FileText, Download,
  Clock, ChevronDown, ChevronUp
} from 'lucide-react';

export default function EscalatedCasesPage() {
  const [expandedCase, setExpandedCase] = useState<string | null>(null);
  const [casesList, setCasesList] = useState<any[]>([]);

  useEffect(() => {
    casesApi.getCases().then((list) => {
      if (list && list.length > 0) {
        setCasesList(list);
      }
    }).catch(() => {});
  }, []);

  const escalatedCases = casesList.map((c: any) => ({
    id: c.protected_case_id || c.id,
    rawId: c.id,
    childId: c.child_id ? `CHILD-${c.child_id.slice(0, 6)}` : '#C8291',
    status: c.status || 'escalated',
    riskLevel: (c.risk_level || c.priority || 'CRITICAL').toLowerCase(),
    description: c.description || c.title || 'Case auto-generated from incoming child safety report.',
    incidentCount: c.incidents?.length || 1,
    createdAt: c.created_at || new Date().toISOString(),
    updatedAt: c.updated_at || new Date().toISOString(),
    tags: ['grooming', 'coercion'],
    assignedModeratorId: c.moderator_id || 'MOD-GA-01',
  }));

  return (
    <div className="min-h-screen bg-dots-pattern">
      <TopBar title="Escalated Cases" subtitle={`${escalatedCases.length} cases requiring authority attention`} />

      <div className="p-3 sm:p-6 space-y-4 sm:space-y-6">
        {/* Summary */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20">
            <AlertTriangle size={14} className="text-red-400" />
            <span className="text-xs font-semibold text-red-300">{escalatedCases.filter(c => c.riskLevel === 'critical').length} Critical</span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20">
            <Shield size={14} className="text-amber-400" />
            <span className="text-xs font-semibold text-amber-300">{escalatedCases.filter(c => c.status === 'escalated').length} Escalated</span>
          </div>
        </div>

        {/* Case Accordion */}
        {escalatedCases.map((c, idx) => (
          <div key={c.id} className="glass-card overflow-hidden">
            {/* Header - clickable */}
            <button
              onClick={() => setExpandedCase(expandedCase === c.id ? null : c.id)}
              className="w-full flex flex-col sm:flex-row sm:items-center justify-between p-4 sm:p-5 text-left hover:bg-slate-800/40 transition-all gap-3"
            >
              <div className="flex items-start sm:items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center flex-shrink-0 mt-0.5 sm:mt-0">
                  <AlertTriangle size={16} className="text-red-400" />
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <span className="text-xs sm:text-sm font-bold text-slate-100">{c.id}</span>
                    <span className="text-xs text-blue-400 font-semibold">{c.childId}</span>
                    <StatusBadge status={c.status} />
                    <RiskBadge level={c.riskLevel} />
                  </div>
                  <p className="text-xs text-slate-400 max-w-xl truncate">{c.description}</p>
                </div>
              </div>
              <div className="flex items-center justify-between sm:justify-end gap-4 border-t sm:border-t-0 border-slate-800 pt-2 sm:pt-0">
                <div className="text-left sm:text-right">
                  <p className="text-[10px] text-slate-500 uppercase">Incidents</p>
                  <p className="text-xs font-bold text-slate-200">{c.incidentCount}</p>
                </div>
                <div className="text-left sm:text-right">
                  <p className="text-[10px] text-slate-500 uppercase">Updated</p>
                  <p className="text-xs text-slate-300">{timeAgo(c.updatedAt)}</p>
                </div>
                {expandedCase === c.id ? (
                  <ChevronUp size={18} className="text-slate-400" />
                ) : (
                  <ChevronDown size={18} className="text-slate-400" />
                )}
              </div>
            </button>

            {/* Expanded Detail */}
            {expandedCase === c.id && (
              <div className="border-t border-slate-800 p-4 sm:p-5 space-y-4 sm:space-y-6 bg-slate-900/40">
                {/* Case Details Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Child ID</p>
                    <p className="text-xs sm:text-sm font-semibold text-blue-400">{c.childId}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Created</p>
                    <p className="text-xs text-slate-300">{formatDateTime(c.createdAt)}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Tags</p>
                    <div className="flex flex-wrap gap-1 mt-0.5">
                      {c.tags.map((tag: string) => (
                        <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 capitalize">{getIncidentLabel(tag as any)}</span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider font-semibold">Moderator</p>
                    <p className="text-xs text-slate-300">{c.assignedModeratorId}</p>
                  </div>
                </div>

                {/* Description */}
                <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.04]">
                  <p className="text-xs text-slate-300 leading-relaxed">{c.description}</p>
                </div>

                {/* Timeline preview */}
                <div>
                  <h4 className="text-xs font-semibold text-white mb-3 flex items-center gap-2">
                    <Clock size={14} className="text-cyan-400" />
                    Case Timeline
                  </h4>
                  <Timeline events={[
                    {
                      id: `t-${c.id}`,
                      caseId: c.rawId,
                      type: 'status_change',
                      title: 'Case Registered & AI Monitored',
                      description: c.description,
                      timestamp: c.createdAt,
                      source: 'Safety Engine',
                      trustLevel: 'human_verified',
                    }
                  ]} />
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 pt-3 border-t border-white/5">
                  <button className="btn-primary !text-xs">
                    <FileText size={12} /> Full Investigation Report
                  </button>
                  <button className="btn-secondary !text-xs">
                    <Download size={12} /> Export Case
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
