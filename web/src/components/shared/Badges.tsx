'use client';

import React from 'react';
import { getRiskBgClass, getTrustBgClass, getTrustLabel, getStatusBgClass, getStatusLabel, getFlagBgClass, getFlagLabel } from '@/lib/utils';
import { RiskLevel, TrustLevel, CaseStatus, FlagType } from '@/types';
import { AlertTriangle, ShieldCheck, Brain, FileCheck } from 'lucide-react';

// ===== Risk Level Badge =====
export function RiskBadge({ level }: { level: RiskLevel }) {
  return (
    <span className={`badge ${getRiskBgClass(level)} uppercase`}>
      {level === 'critical' && <AlertTriangle size={10} />}
      {level}
    </span>
  );
}

// ===== Trust Level Badge =====
export function TrustBadge({ level }: { level: TrustLevel }) {
  const iconMap: Record<string, React.ComponentType<{ size?: number; className?: string }>> = {
    raw: FileCheck,
    ai_derived: Brain,
    human_verified: ShieldCheck,
    moderator_verified: ShieldCheck,
    official: ShieldCheck,
  };

  const Icon = iconMap[level] || ShieldCheck;

  return (
    <span className={`badge ${getTrustBgClass(level)}`}>
      <Icon size={10} />
      {getTrustLabel(level)}
    </span>
  );
}

// ===== Case Status Badge =====
export function StatusBadge({ status }: { status: CaseStatus }) {
  return (
    <span className={`badge ${getStatusBgClass(status)}`}>
      {getStatusLabel(status)}
    </span>
  );
}

// ===== Flag Type Badge =====
export function FlagBadge({ type }: { type: FlagType }) {
  return (
    <span className={`badge ${getFlagBgClass(type)}`}>
      {getFlagLabel(type)}
    </span>
  );
}

// ===== Risk Gauge =====
export function RiskGauge({ level, score }: { level: RiskLevel; score?: number }) {
  const percent = score || { low: 25, medium: 50, high: 75, critical: 95 }[level];
  const color = {
    low: '#10b981',
    medium: '#f59e0b',
    high: '#ef4444',
    critical: '#dc2626',
  }[level];

  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${percent}%`,
            background: `linear-gradient(90deg, ${color}88, ${color})`,
            boxShadow: `0 0 8px ${color}40`,
          }}
        />
      </div>
      <span className="text-xs font-semibold" style={{ color }}>{percent}%</span>
    </div>
  );
}

// ===== Confidence Meter =====
export function ConfidenceMeter({ value }: { value: number }) {
  const percent = Math.round(value * 100);
  const color = percent >= 80 ? '#ef4444' : percent >= 60 ? '#f59e0b' : '#10b981';

  return (
    <div className="flex items-center gap-2">
      <div className="w-16 h-1.5 rounded-full bg-white/5 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${percent}%`,
            background: color,
            boxShadow: `0 0 6px ${color}30`,
          }}
        />
      </div>
      <span className="text-[11px] font-mono font-semibold" style={{ color }}>{percent}%</span>
    </div>
  );
}
