'use client';

import React from 'react';
import { TimelineEvent } from '@/types';
import { TrustBadge } from './Badges';
import { formatDateTime } from '@/lib/utils';
import {
  AlertTriangle, MessageSquare, FileText, Shield,
  CheckCircle, Radio, Image, ArrowUpRight, Brain
} from 'lucide-react';

interface TimelineProps {
  events: TimelineEvent[];
}

function getEventIcon(type: TimelineEvent['type']) {
  switch (type) {
    case 'report': return <FileText size={16} />;
    case 'ai_flag': return <Brain size={16} />;
    case 'moderator_note': return <MessageSquare size={16} />;
    case 'escalation': return <ArrowUpRight size={16} />;
    case 'resolution': return <CheckCircle size={16} />;
    case 'sos': return <AlertTriangle size={16} />;
    case 'communication': return <Radio size={16} />;
    case 'evidence': return <Image size={16} />;
    case 'status_change': return <Shield size={16} />;
    default: return <FileText size={16} />;
  }
}

function getEventColor(type: TimelineEvent['type']) {
  switch (type) {
    case 'report': return '#3b82f6';
    case 'ai_flag': return '#8b5cf6';
    case 'moderator_note': return '#10b981';
    case 'escalation': return '#ef4444';
    case 'resolution': return '#10b981';
    case 'sos': return '#ef4444';
    case 'communication': return '#06b6d4';
    case 'evidence': return '#f59e0b';
    case 'status_change': return '#6366f1';
    default: return '#64748b';
  }
}

export default function Timeline({ events }: TimelineProps) {
  const sorted = [...events].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-5 top-2 bottom-2 w-px bg-gradient-to-b from-cyan-500/20 via-slate-700/30 to-transparent" />

      <div className="space-y-1">
        {sorted.map((event, idx) => {
          const color = getEventColor(event.type);
          return (
            <div
              key={event.id}
              className="relative flex gap-4 pl-0 py-3 group animate-fade-in"
              style={{ animationDelay: `${idx * 0.05}s` }}
            >
              {/* Icon dot */}
              <div className="relative z-10 flex-shrink-0">
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center transition-all group-hover:scale-110"
                  style={{ background: `${color}15`, color }}
                >
                  {getEventIcon(event.type)}
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 glass-card p-4 !rounded-xl group-hover:border-white/10">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h4 className="text-sm font-semibold text-white">{event.title}</h4>
                    <TrustBadge level={event.trustLevel} />
                  </div>
                  <span className="text-[11px] text-slate-500 whitespace-nowrap flex-shrink-0">
                    {formatDateTime(event.timestamp)}
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">{event.description}</p>
                <p className="text-[10px] text-slate-600 mt-2">Source: {event.source}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
