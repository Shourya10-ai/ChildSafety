'use client';

import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  delta?: number;
  deltaLabel?: string;
  icon: React.ReactNode;
  accentColor?: string;
  variant?: 'default' | 'danger' | 'success' | 'warning';
}

export default function StatCard({
  title,
  value,
  delta,
  deltaLabel,
  icon,
  accentColor = '#2563eb',
  variant = 'default',
}: StatCardProps) {
  const isPositive = delta !== undefined && delta > 0;
  const isNegative = delta !== undefined && delta < 0;
  const isNeutral = delta === 0;

  return (
    <div className="glass-card p-4 sm:p-5 relative overflow-hidden bg-slate-900 border border-slate-800 rounded-2xl shadow-sm">
      <div className="flex items-start justify-between mb-2 sm:mb-3">
        <div
          className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl flex items-center justify-center bg-slate-800"
          style={{ color: accentColor }}
        >
          {icon}
        </div>
        {delta !== undefined && (
          <div className={`flex items-center gap-1 text-xs font-semibold px-2 py-0.5 sm:py-1 rounded-md ${
            isPositive ? 'text-rose-400 bg-rose-500/10' :
            isNegative ? 'text-emerald-400 bg-emerald-500/10' :
            'text-slate-400 bg-slate-800'
          }`}>
            {isPositive && <TrendingUp size={12} />}
            {isNegative && <TrendingDown size={12} />}
            {isNeutral && <Minus size={12} />}
            {isPositive ? `+${delta}` : isNeutral ? '0' : delta}
          </div>
        )}
      </div>

      <p className="text-2xl sm:text-3xl font-bold text-white tracking-tight">{value}</p>
      <p className="text-xs text-slate-400 mt-1 font-medium truncate">{title}</p>
      {deltaLabel && (
        <p className="text-[10px] text-slate-500 mt-0.5 truncate">{deltaLabel}</p>
      )}
    </div>
  );
}
