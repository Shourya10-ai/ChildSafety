import { RiskLevel, TrustLevel, CaseStatus, FlagType, IncidentType } from '@/types';

// ===== Date/Time Formatting =====
export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function timeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return formatDate(dateStr);
}

// ===== Risk Level Utilities =====
export function getRiskColor(level: RiskLevel): string {
  switch (level) {
    case 'low': return '#10b981';
    case 'medium': return '#f59e0b';
    case 'high': return '#ef4444';
    case 'critical': return '#dc2626';
  }
}

export function getRiskBgClass(level: RiskLevel): string {
  switch (level) {
    case 'low': return 'badge-emerald';
    case 'medium': return 'badge-amber';
    case 'high': return 'badge-red';
    case 'critical': return 'badge-red';
  }
}

// ===== Trust Level Utilities =====
export function getTrustLabel(level: TrustLevel): string {
  switch (level) {
    case 'raw': return 'RAW';
    case 'ai_derived': return 'AI-DERIVED';
    case 'human_verified': return 'VERIFIED';
    case 'moderator_verified': return 'MOD-VERIFIED';
    case 'official': return 'OFFICIAL';
    default: return (level as string)?.toUpperCase() || 'VERIFIED';
  }
}

export function getTrustBgClass(level: TrustLevel): string {
  switch (level) {
    case 'raw': return 'badge-blue';
    case 'ai_derived': return 'badge-violet';
    case 'human_verified': return 'badge-emerald';
    case 'moderator_verified': return 'badge-emerald';
    case 'official': return 'badge-cyan';
    default: return 'badge-emerald';
  }
}

// ===== Status Utilities =====
export function getStatusLabel(status: CaseStatus): string {
  switch (status) {
    case 'active': return 'Active';
    case 'under_review': return 'Under Review';
    case 'escalated': return 'Escalated';
    case 'resolved': return 'Resolved';
    case 'closed': return 'Closed';
  }
}

export function getStatusBgClass(status: CaseStatus): string {
  switch (status) {
    case 'active': return 'badge-cyan';
    case 'under_review': return 'badge-amber';
    case 'escalated': return 'badge-red';
    case 'resolved': return 'badge-emerald';
    case 'closed': return 'badge-blue';
  }
}

// ===== Flag Type Utilities =====
export function getFlagLabel(type: FlagType): string {
  switch (type) {
    case 'bullying': return 'Bullying';
    case 'grooming': return 'Grooming';
    case 'threat': return 'Threat';
    case 'harassment': return 'Harassment';
    case 'inappropriate_content': return 'Inappropriate Content';
  }
}

export function getFlagBgClass(type: FlagType): string {
  switch (type) {
    case 'bullying': return 'badge-amber';
    case 'grooming': return 'badge-red';
    case 'threat': return 'badge-red';
    case 'harassment': return 'badge-violet';
    case 'inappropriate_content': return 'badge-amber';
  }
}

// ===== Incident Type Utilities =====
export function getIncidentLabel(type: IncidentType): string {
  switch (type) {
    case 'bullying': return 'Bullying';
    case 'cyberbullying': return 'Cyberbullying';
    case 'grooming': return 'Grooming';
    case 'threat': return 'Threat';
    case 'harassment': return 'Harassment';
    case 'abuse': return 'Abuse';
    case 'missing_child': return 'Missing Child';
    case 'sos': return 'SOS';
    case 'other': return 'Other';
  }
}

// ===== Number Formatting =====
export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function formatDelta(value: number): string {
  if (value > 0) return `+${value}`;
  return value.toString();
}
