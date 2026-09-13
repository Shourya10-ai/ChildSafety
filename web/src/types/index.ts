// ===== Core Types for Child Safety Platform =====

export type UserRole = 'moderator' | 'authority' | 'admin';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar?: string;
  department?: string;
  assignedChildren?: number;
}

export type CaseStatus = 'active' | 'under_review' | 'escalated' | 'resolved' | 'closed';
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type TrustLevel = 'raw' | 'ai_derived' | 'human_verified' | 'official' | 'moderator_verified';
export type IncidentType = 'bullying' | 'cyberbullying' | 'grooming' | 'threat' | 'harassment' | 'abuse' | 'missing_child' | 'sos' | 'other';
export type FlagType = 'bullying' | 'grooming' | 'threat' | 'harassment' | 'inappropriate_content';
export type FlagStatus = 'pending' | 'confirmed' | 'false_positive' | 'escalated';

export interface ProtectedChild {
  id: string; // e.g., "#C8291"
  age?: number;
  riskLevel: RiskLevel;
  assignedModeratorId: string;
  activeCases: number;
  totalIncidents: number;
  lastActivity: string; // ISO date
  riskTrend: 'increasing' | 'stable' | 'decreasing';
  status: 'active' | 'monitoring' | 'resolved';
}

export interface CaseRecord {
  id: string;
  childId: string;
  status: CaseStatus;
  riskLevel: RiskLevel;
  createdAt: string;
  updatedAt: string;
  assignedModeratorId: string;
  incidentCount: number;
  description: string;
  tags: IncidentType[];
}

export interface TimelineEvent {
  id: string;
  caseId: string;
  type: 'report' | 'ai_flag' | 'moderator_note' | 'escalation' | 'resolution' | 'sos' | 'communication' | 'evidence' | 'status_change';
  trustLevel: TrustLevel;
  title: string;
  description: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
  source: string; // who/what created this
}

export interface AIFlag {
  id: string;
  childId: string;
  caseId: string;
  type: FlagType;
  confidence: number; // 0-1
  riskLevel: RiskLevel;
  contentSnippet: string;
  detectedAt: string;
  status: FlagStatus;
  moderatorFeedback?: string;
  language?: string;
}

export interface ModeratorNote {
  id: string;
  caseId: string;
  moderatorId: string;
  content: string;
  createdAt: string;
  updatedAt?: string;
  type: 'assessment' | 'follow_up' | 'recommendation' | 'observation';
}

export interface Evidence {
  id: string;
  caseId: string;
  type: 'image' | 'screenshot' | 'text' | 'audio' | 'video' | 'document';
  source: string;
  capturedAt: string;
  fileHash?: string;
  aiAnalysis?: {
    threatProbability?: number;
    bullyingProbability?: number;
    groomingProbability?: number;
  };
  moderatorVerification?: {
    verified: boolean;
    verifiedBy: string;
    verifiedAt: string;
    notes?: string;
  };
  trustLevel: TrustLevel;
  thumbnailUrl?: string;
  description?: string;
}

export interface MissingChild {
  id: string;
  caseId: string;
  photoUrl?: string;
  description: string;
  age: number;
  clothing?: string;
  lastKnownLocation: {
    lat: number;
    lng: number;
    address: string;
  };
  lastSeenAt: string;
  reportedAt: string;
  status: 'active' | 'found' | 'investigating';
  cctvCandidates: CCTVCandidate[];
  identifyingCharacteristics?: string[];
}

export interface CCTVCandidate {
  id: string;
  imageUrl?: string;
  location: {
    lat: number;
    lng: number;
    address: string;
  };
  capturedAt: string;
  similarityScore: number;
  verified: boolean;
  cameraId: string;
}

export interface GraphNode {
  id: string;
  type: 'child' | 'incident' | 'account' | 'location' | 'evidence' | 'suspect' | 'platform';
  label: string;
  metadata?: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
  weight?: number;
}

export interface ChatMessage {
  id: string;
  senderId: string;
  senderRole: 'moderator' | 'child';
  content: string;
  timestamp: string;
  read: boolean;
}

export interface Notification {
  id: string;
  type: 'ai_flag' | 'sos' | 'escalation' | 'case_update' | 'message' | 'assignment';
  title: string;
  description: string;
  timestamp: string;
  read: boolean;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  actionUrl?: string;
}

export interface DashboardStats {
  activeCases: number;
  activeCasesDelta: number;
  newFlags: number;
  newFlagsDelta: number;
  urgentCases: number;
  urgentCasesDelta: number;
  assignedChildren: number;
  assignedChildrenDelta: number;
  resolvedThisWeek: number;
  resolvedDelta: number;
  escalatedCases: number;
  escalatedDelta: number;
  missingChildren?: number;
  missingChildrenDelta?: number;
  activeInvestigations?: number;
  activeInvestigationsDelta?: number;
}

export interface RiskTrendDataPoint {
  date: string;
  riskScore: number;
  incidents: number;
}
