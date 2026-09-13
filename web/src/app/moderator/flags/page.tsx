'use client';

import React, { useState, useEffect } from 'react';
import TopBar from '@/components/layout/TopBar';
import { RiskBadge, FlagBadge, ConfidenceMeter } from '@/components/shared/Badges';
import { incidentsApi, reportsApi, casesApi } from '@/lib/api';
import { realtimeService } from '@/lib/websocket';
import { timeAgo } from '@/lib/utils';
import { Flag, Brain, Check, X, ArrowUpRight, Filter, RefreshCw } from 'lucide-react';
import { FlagStatus } from '@/types';

// Derive risk level from severity string
function mapRisk(severity?: string): string {
  if (!severity) return 'medium';
  const s = severity.toLowerCase();
  if (s === 'critical' || s === 'extreme') return 'critical';
  if (s === 'high') return 'high';
  if (s === 'medium' || s === 'moderate') return 'medium';
  return 'low';
}

// Extract AI confidence from ai_flags object (backend may use different field names)
function mapConfidence(ai_flags?: any, trust_level?: string): number | null {
  if (!ai_flags && !trust_level) return null;
  if (typeof ai_flags === 'object' && ai_flags !== null) {
    const raw = ai_flags.threat_probability ?? ai_flags.confidence ?? ai_flags.score ?? null;
    if (typeof raw === 'number') return raw;
  }
  // Rough estimate from trust_level if no numeric confidence
  if (trust_level === 'official' || trust_level === 'human_verified') return 0.97;
  if (trust_level === 'moderator_verified') return 0.93;
  if (trust_level === 'ai_derived') return 0.75;
  return null;
}

export default function AIFlagsPage() {
  const [flags, setFlags] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedFlag, setSelectedFlag] = useState<any | null>(null);

  const loadFlags = async () => {
    setIsLoading(true);
    try {
      const [incidents, reports] = await Promise.all([
        incidentsApi.getActive(50).catch(() => []),
        reportsApi.getReports(50).catch(() => []),
      ]);

      const mappedIncidents = (incidents || []).map((inc: any) => ({
        id: inc.id,
        source: 'incident' as const,
        childId: inc.child_id ? `#${String(inc.child_id).slice(0, 8).toUpperCase()}` : null,
        caseId: inc.case_id || null,
        type: inc.incident_type || 'unknown',
        riskLevel: mapRisk(inc.severity),
        confidence: mapConfidence(inc.ai_flags, inc.trust_level),
        detectedAt: inc.created_at || inc.occurred_at || new Date().toISOString(),
        status: inc.is_verified ? 'confirmed' : 'pending',
        contentSnippet: inc.description || null,
        platform: inc.source || null,
      }));

      const mappedReports = (reports || []).map((rep: any) => ({
        id: rep.id,
        source: 'report' as const,
        childId: rep.child_id ? `#${String(rep.child_id).slice(0, 8).toUpperCase()}` : null,
        caseId: rep.case_id || null,
        type: rep.category || 'report',
        riskLevel: mapRisk(rep.details?.severity),
        confidence: null, // reports don't carry AI confidence
        detectedAt: rep.created_at || new Date().toISOString(),
        status: rep.status === 'resolved' || rep.status === 'moderator_confirmed' ? 'confirmed' : rep.status === 'false_positive_dismissed' ? 'false_positive' : 'pending',
        contentSnippet: rep.content || rep.details || null,
        platform: rep.reporter_type || null,
      }));

      setFlags([...mappedIncidents, ...mappedReports]);
    } catch (e) {
      setFlags([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadFlags();

    // Subscribe to real-time WebSocket events for automatic live updates
    realtimeService.connect();
    const unsubscribe = realtimeService.subscribe((event) => {
      if (['NEW_REPORT', 'INCIDENT_VERIFIED', 'CASE_STATUS_CHANGED', 'SOS_ALERT'].includes(event)) {
        loadFlags();
      }
    });

    return () => {
      unsubscribe();
    };
  }, []);

  const filtered = flags.filter((f) =>
    statusFilter === 'all' || f.status === statusFilter
  );

  const handleAction = async (flagId: string, action: FlagStatus) => {
    const flag = flags.find((f) => f.id === flagId);
    if (!flag) return;

    // Immediately reflect state in local UI
    setFlags((prev) =>
      prev.map((f) => (f.id === flagId ? { ...f, status: action } : f))
    );
    setSelectedFlag(null);

    try {
      if (flag.source === 'incident') {
        if (action === 'confirmed') {
          await incidentsApi.verify(flagId, 'moderator_verified');
        }
      }

      if (flag.caseId) {
        if (action === 'confirmed') {
          await casesApi.transitionStatus(flag.caseId, {
            to_status: 'moderator_confirmed',
            reason: 'Verified real threat by safety moderator.',
          });
        } else if (action === 'false_positive') {
          await casesApi.transitionStatus(flag.caseId, {
            to_status: 'false_positive_dismissed',
            reason: 'Dismissed as false positive after review.',
            dismissal_category: 'FALSE_ALARM',
          });
        } else if (action === 'escalated') {
          await casesApi.escalate(flag.caseId, {
            escalate_to: 'authority',
            reason: 'Escalated to Police Authority for immediate intervention.',
          });
        }
      }
    } catch (e) {
      console.error('Failed to push action to backend:', e);
    }
  };

  const pendingCount = flags.filter(f => f.status === 'pending').length;
  const confirmedCount = flags.filter(f => f.status === 'confirmed').length;
  const fpCount = flags.filter(f => f.status === 'false_positive').length;

  return (
    <div className="min-h-screen bg-dots-pattern">
      <TopBar title="AI Flag Review" subtitle={`${pendingCount} flags pending human verification (GET /api/v1/incidents/active)`} />

      <div className="p-3 sm:p-6 space-y-4 sm:space-y-6">
        {/* Summary bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-3.5 sm:p-4 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-violet-500/10 border border-violet-500/20">
              <Brain size={14} className="text-violet-400" />
              <span className="text-xs font-semibold text-violet-300">{pendingCount} Pending</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
              <Check size={14} className="text-emerald-400" />
              <span className="text-xs font-semibold text-emerald-300">{confirmedCount} Confirmed</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700">
              <X size={14} className="text-slate-400" />
              <span className="text-xs font-semibold text-slate-300">{fpCount} False Positive</span>
            </div>
            <button
              onClick={loadFlags}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-400 hover:text-slate-200 transition-all"
            >
              <RefreshCw size={12} className={isLoading ? 'animate-spin' : ''} />
              Refresh
            </button>
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto whitespace-nowrap no-scrollbar pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-800">
            <Filter size={14} className="text-slate-500 flex-shrink-0 mr-1" />
            {['all', 'pending', 'confirmed', 'false_positive', 'escalated'].map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                  statusFilter === s
                    ? 'bg-blue-600/20 text-blue-400 border border-blue-500/40'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-transparent'
                }`}
              >
                {s === 'all' ? 'All' : s === 'false_positive' ? 'False Positive' : s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Flags List + Detail Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 sm:gap-6">
          {/* Flags list */}
          <div className="lg:col-span-3 space-y-3">
            {/* Loading skeleton */}
            {isLoading && (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="glass-card p-5 animate-pulse">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-8 h-8 rounded-lg bg-slate-800" />
                      <div className="space-y-1.5 flex-1">
                        <div className="h-3 bg-slate-800 rounded w-1/3" />
                        <div className="h-2 bg-slate-800 rounded w-1/4" />
                      </div>
                    </div>
                    <div className="h-10 bg-slate-800 rounded-lg" />
                  </div>
                ))}
              </div>
            )}

            {/* Empty state */}
            {!isLoading && filtered.length === 0 && (
              <div className="glass-card p-10 text-center">
                <Flag size={36} className="text-slate-700 mx-auto mb-3" />
                <p className="text-sm font-semibold text-slate-400">No AI flags found</p>
                <p className="text-xs text-slate-600 mt-1">
                  {statusFilter === 'all'
                    ? 'No incidents or reports have been flagged yet. Live flags will appear here automatically.'
                    : `No flags with status "${statusFilter}". Try a different filter.`}
                </p>
              </div>
            )}

            {!isLoading && filtered.map((flag) => (
              <div
                key={flag.id}
                onClick={() => setSelectedFlag(flag)}
                className={`glass-card p-4 sm:p-5 cursor-pointer transition-all ${
                  selectedFlag?.id === flag.id ? '!border-blue-500/60 shadow-[0_0_20px_rgba(37,99,235,0.15)] bg-slate-800/80' : ''
                } ${flag.status === 'pending' ? 'border-l-4 !border-l-violet-500' : ''}`}
              >
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center flex-shrink-0">
                      <Flag size={14} className="text-violet-400" />
                    </div>
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-xs sm:text-sm font-semibold text-slate-100">
                          {flag.childId || <span className="text-slate-500 italic">Protected ID</span>}
                        </span>
                        <FlagBadge type={flag.type} />
                        <RiskBadge level={flag.riskLevel} />
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase ${
                          flag.source === 'incident' ? 'bg-violet-500/10 text-violet-400' : 'bg-blue-500/10 text-blue-400'
                        }`}>
                          {flag.source}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-500 mt-0.5 font-mono">
                        {flag.id.slice(0, 16)}… · {timeAgo(flag.detectedAt)}
                        {flag.caseId && <> · Case: {flag.caseId.slice(0, 8)}</>}
                      </p>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    {flag.confidence !== null ? (
                      <ConfidenceMeter value={flag.confidence} />
                    ) : (
                      <span className="text-[10px] text-slate-600 italic">No AI score</span>
                    )}
                  </div>
                </div>

                {flag.contentSnippet ? (
                  <p className="text-xs text-slate-300 leading-relaxed mb-3 italic bg-slate-900/40 p-2.5 rounded-lg border border-slate-800/80">
                    &ldquo;{flag.contentSnippet}&rdquo;
                  </p>
                ) : (
                  <p className="text-xs text-slate-600 italic mb-3">No content preview available</p>
                )}

                {flag.platform && (
                  <span className="text-[10px] text-slate-400 bg-slate-800 px-2 py-0.5 rounded font-mono">
                    Source: {flag.platform}
                  </span>
                )}

                {/* Status / Actions */}
                {flag.status === 'pending' ? (
                  <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-slate-800">
                    <button
                      onClick={(e) => { e.stopPropagation(); handleAction(flag.id, 'confirmed'); }}
                      className="btn-primary !py-1.5 !px-3 !text-xs !rounded-lg flex-1 sm:flex-none justify-center"
                    >
                      <Check size={12} /> Confirm & Verify
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleAction(flag.id, 'false_positive'); }}
                      className="btn-secondary !py-1.5 !px-3 !text-xs !rounded-lg flex-1 sm:flex-none justify-center"
                    >
                      <X size={12} /> False Positive
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleAction(flag.id, 'escalated'); }}
                      className="btn-danger !py-1.5 !px-3 !text-xs !rounded-lg w-full sm:w-auto justify-center"
                    >
                      <ArrowUpRight size={12} /> Escalate
                    </button>
                  </div>
                ) : (
                  <div className="mt-3 pt-3 border-t border-slate-800">
                    <span className={`text-[11px] font-semibold ${
                      flag.status === 'confirmed' ? 'text-emerald-400' :
                      flag.status === 'false_positive' ? 'text-slate-400' :
                      'text-red-400'
                    }`}>
                      ✓ {flag.status === 'false_positive' ? 'False Positive' : flag.status.charAt(0).toUpperCase() + flag.status.slice(1)}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Detail Panel */}
          <div className="lg:col-span-2">
            {selectedFlag ? (
              <div className="glass-card p-6 sticky top-20 animate-fade-in-scale">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <Brain size={16} className="text-violet-400" />
                  Flag Detail
                  {selectedFlag.source === 'incident' && (
                    <span className="text-[10px] text-slate-500">(PUT /api/v1/incidents/id/verify)</span>
                  )}
                </h3>

                <div className="space-y-4">
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Source Type</p>
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded uppercase ${
                      selectedFlag.source === 'incident' ? 'bg-violet-500/10 text-violet-400' : 'bg-blue-500/10 text-blue-400'
                    }`}>
                      {selectedFlag.source}
                    </span>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Child ID</p>
                    <p className="text-sm font-semibold text-white font-mono">
                      {selectedFlag.childId || <span className="text-slate-500 italic">Protected (masked)</span>}
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Case ID</p>
                    <p className="text-sm font-mono text-cyan-400">
                      {selectedFlag.caseId || <span className="text-slate-500 italic">Unlinked</span>}
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Detection Type</p>
                    <FlagBadge type={selectedFlag.type} />
                  </div>
                  {selectedFlag.confidence !== null && (
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">AI Confidence</p>
                      <ConfidenceMeter value={selectedFlag.confidence} />
                    </div>
                  )}
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Risk Level</p>
                    <RiskBadge level={selectedFlag.riskLevel} />
                  </div>
                  {selectedFlag.platform && (
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Platform / Source</p>
                      <p className="text-xs text-slate-300">{selectedFlag.platform}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Content</p>
                    {selectedFlag.contentSnippet ? (
                      <p className="text-xs text-slate-300 italic bg-white/[0.03] p-3 rounded-lg leading-relaxed">
                        &ldquo;{selectedFlag.contentSnippet}&rdquo;
                      </p>
                    ) : (
                      <p className="text-xs text-slate-600 italic">No content available</p>
                    )}
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Record ID</p>
                    <p className="text-[10px] font-mono text-slate-500 break-all">{selectedFlag.id}</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="glass-card p-6 text-center">
                <Brain size={32} className="text-slate-700 mx-auto mb-3" />
                <p className="text-sm text-slate-500">Select a flag to view details</p>
                <p className="text-xs text-slate-600 mt-1">Verification actions are performed per flag</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
