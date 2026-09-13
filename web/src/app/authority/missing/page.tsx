'use client';

import React, { useState, useEffect } from 'react';
import TopBar from '@/components/layout/TopBar';
import { missingChildrenApi, MissingChildApiRecord } from '@/lib/api';
import { formatDateTime, timeAgo } from '@/lib/utils';
import {
  Eye, MapPin, Camera, Clock, Users, CheckCircle, X,
  ChevronDown, ChevronUp, AlertTriangle, Plus, ShieldCheck, Check
} from 'lucide-react';

export default function MissingChildrenPage() {
  const [childrenList, setChildrenList] = useState<any[]>([]);
  const [expandedChild, setExpandedChild] = useState<string | null>(null);

  // File Alert Modal State
  const [showFileModal, setShowFileModal] = useState(false);
  const [childName, setChildName] = useState('');
  const [description, setDescription] = useState('');
  const [age, setAge] = useState(10);
  const [lastAddress, setLastAddress] = useState('');
  const [isFiling, setIsFiling] = useState(false);

  // Load API missing children alerts
  useEffect(() => {
    missingChildrenApi.listAlerts({ limit: 50 }).then((data) => {
      if (data) {
        setChildrenList(data);
        if (data.length > 0) setExpandedChild(data[0].id);
      }
    }).catch(() => {});
  }, []);

  const handleFileAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!childName || !description) return;
    setIsFiling(true);

    try {
      await missingChildrenApi.fileAlert({
        child_name: childName,
        description,
        age_when_missing: Number(age),
        last_known_address: lastAddress,
        state: 'Delhi',
        district: 'Delhi',
      });
    } catch (err) {
      console.warn('API missing child filing fallback');
    }

    const newRecord = {
      id: `MISSING-${Date.now()}`,
      caseId: `CASE-${Date.now()}`,
      description: `${childName}: ${description}`,
      age: Number(age),
      lastKnownLocation: { lat: 28.6139, lng: 77.2090, address: lastAddress || 'Lodhi Garden, New Delhi' },
      lastSeenAt: new Date().toISOString(),
      reportedAt: new Date().toISOString(),
      status: 'active' as const,
      cctvCandidates: [],
    };

    setChildrenList([newRecord, ...childrenList]);
    setShowFileModal(false);
    setIsFiling(false);
    setChildName('');
    setDescription('');
  };

  const handleVerifySighting = async (sightingId: string, isMatch: boolean) => {
    try {
      await missingChildrenApi.verifySighting(sightingId, {
        is_match: isMatch,
        notes: isMatch ? 'Verified by law enforcement' : 'Mismatch',
      });
    } catch (e) {}
  };

  const handleResolve = async (childId: string) => {
    try {
      await missingChildrenApi.resolveMissing(childId, {
        resolution_notes: 'Child safely secured and reunited with family.',
      });
    } catch (e) {}

    setChildrenList((prev) =>
      prev.map((c) => (c.id === childId ? { ...c, status: 'found' } : c))
    );
  };

  return (
    <div className="min-h-screen bg-dots-pattern">
      <TopBar title="Missing Children & Citizen Sightings" subtitle="Live emergency missing child alerts (GET /api/v1/missing-children/)" />

      <div className="p-6 space-y-6">
        {/* Alert banner + File Action */}
        <div className="glass-card p-4 !border-amber-500/20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center flex-shrink-0">
              <AlertTriangle size={18} className="text-amber-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-amber-300">
                {childrenList.filter(mc => mc.status === 'active' || mc.status === 'ACTIVE').length} Active Missing Child Alerts
              </p>
              <p className="text-[11px] text-slate-400">Citizen sightings & CCTV candidates require human moderator verification</p>
            </div>
          </div>
          <button
            onClick={() => setShowFileModal(true)}
            className="btn-danger !text-xs flex items-center gap-1 cursor-pointer"
          >
            <Plus size={14} /> File Emergency Missing Alert
          </button>
        </div>

        {/* Missing Children Cards */}
        <div className="space-y-4">
          {childrenList.map((mc, idx) => (
            <div key={mc.id} className="glass-card overflow-hidden animate-fade-in" style={{ animationDelay: `${idx * 0.1}s` }}>
              {/* Header */}
              <button
                onClick={() => setExpandedChild(expandedChild === mc.id ? null : mc.id)}
                className="w-full flex items-center justify-between p-5 text-left hover:bg-white/[0.02] transition-all"
              >
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-amber-500/20 to-red-500/20 flex items-center justify-center flex-shrink-0">
                    <Eye size={24} className="text-amber-400" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg font-bold text-white">{mc.id}</span>
                      <span className={`badge ${mc.status === 'active' || mc.status === 'ACTIVE' ? 'badge-red' : 'badge-emerald'}`}>
                        {mc.status}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400">Age {mc.age || mc.age_when_missing} · {mc.lastKnownLocation?.address || mc.last_known_address || 'New Delhi'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {mc.status !== 'found' && mc.status !== 'FOUND' && (
                    <button
                      onClick={(e) => { e.stopPropagation(); handleResolve(mc.id); }}
                      className="btn-primary !py-1 !px-3 !text-xs"
                    >
                      <CheckCircle size={12} /> Mark Found
                    </button>
                  )}
                  {expandedChild === mc.id ? <ChevronUp size={18} className="text-slate-400" /> : <ChevronDown size={18} className="text-slate-400" />}
                </div>
              </button>

              {/* Expanded */}
              {expandedChild === mc.id && (
                <div className="border-t border-white/5 p-5 animate-fade-in">
                  <p className="text-sm text-slate-300 mb-3">{mc.description}</p>
                  <p className="text-xs text-slate-400 flex items-center gap-1">
                    <MapPin size={12} className="text-amber-400" /> Last Known Address: {mc.lastKnownLocation?.address || mc.last_known_address || 'New Delhi'}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* FILE EMERGENCY MISSING ALERT MODAL */}
      {showFileModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fade-in">
          <form onSubmit={handleFileAlert} className="glass-strong max-w-lg w-full rounded-3xl p-6 border border-white/10 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
              <Plus size={18} className="text-rose-400" /> File Emergency Missing Child Alert
            </h3>
            <p className="text-xs text-slate-400 mb-4">POST /api/v1/missing-children/</p>

            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Child Name</label>
                <input
                  type="text"
                  value={childName}
                  onChange={(e) => setChildName(e.target.value)}
                  placeholder="e.g. Aman Verma"
                  className="input-field text-xs"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Age</label>
                <input
                  type="number"
                  value={age}
                  onChange={(e) => setAge(Number(e.target.value))}
                  className="input-field text-xs"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Last Known Address</label>
                <input
                  type="text"
                  value={lastAddress}
                  onChange={(e) => setLastAddress(e.target.value)}
                  placeholder="e.g. Lodhi Garden, New Delhi"
                  className="input-field text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Description & Circumstances</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Provide physical description, clothing, and last seen details..."
                  className="input-field min-h-[80px] text-xs"
                  required
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowFileModal(false)}
                className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white"
              >
                Cancel
              </button>
              <button type="submit" disabled={isFiling} className="btn-danger !text-xs">
                {isFiling ? 'Filing Alert...' : 'Publish Emergency Alert'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
