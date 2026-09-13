import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

// Live Backend Base URL
export const BACKEND_BASE_URL = 'https://squishier-clunky-neuter.ngrok-free.dev';
export const WEBSOCKET_URL = 'wss://squishier-clunky-neuter.ngrok-free.dev/api/v1/ws';

// Create Axios Instance
export const api: AxiosInstance = axios.create({
  baseURL: BACKEND_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': '1', // REQUIRED: bypasses ngrok browser warning page
  },
  timeout: 20000,
});

// Request Interceptor: Attach Bearer Token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Auto-Refresh Token on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      typeof window !== 'undefined'
    ) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken && refreshToken !== 'demo-refresh') {
        try {
          const res = await axios.post(
            `${BACKEND_BASE_URL}/api/v1/auth/refresh`,
            { refresh_token: refreshToken },
            {
              headers: {
                'Content-Type': 'application/json',
                'ngrok-skip-browser-warning': '1',
              },
            }
          );
          const { access_token } = res.data;
          if (access_token) {
            localStorage.setItem('access_token', access_token);
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${access_token}`;
            }
            return api(originalRequest);
          }
        } catch (refreshErr) {
          console.warn('[API Interceptor] Refresh failed gracefully:', refreshErr);
        }
      }
    }
    return Promise.reject(error);
  }
);

// ===== API ENDPOINTS TYPE DEFINITIONS =====

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id?: string;
  email?: string;
  full_name?: string;
  role?: 'child' | 'adult' | 'moderator' | 'authority' | 'admin';
  jurisdiction_state?: string;
  jurisdiction_district?: string;
  user?: {
    id: string;
    email: string;
    full_name?: string;
    role: 'child' | 'adult' | 'moderator' | 'authority' | 'admin';
    phone?: string;
  };
}

export interface CaseApiRecord {
  id: string;
  child_id: string;
  moderator_id?: string;
  protected_case_id?: string;
  title?: string;
  description: string;
  status: string;
  priority: string;
  risk_level: string;
  risk_score?: number;
  created_at: string;
  updated_at: string;
  incidents?: any[];
  notes?: any[];
}

export interface SosApiRecord {
  id: string;
  child_id?: string;
  case_id?: string;
  latitude: number;
  longitude: number;
  location_address?: string;
  status: 'ACTIVE' | 'RESOLVED';
  message?: string;
  child_name?: string;
  is_silent_duress: boolean;
  routed_to_alternate_adults_only?: boolean;
  notified_guardians_count?: number;
  created_at: string;
  resolved_at?: string | null;
}

export interface IncidentApiRecord {
  id: string;
  case_id: string;
  incident_type: string;
  severity: string;
  description: string;
  ai_flags?: any;
  trust_level?: string;
  source?: string;
  occurred_at?: string;
  is_verified?: boolean;
  verified_by?: string;
  verified_at?: string;
  created_at?: string;
}

export interface ReportApiRecord {
  id: string;
  incident_id?: string;
  case_id?: string;
  reporter_id?: string;
  reporter_type?: string;
  category?: string;
  content: string;
  details?: string;
  child_id?: string;
  contact_info?: string;
  is_anonymous: boolean;
  status?: string;
  created_at: string;
}

export interface NotificationApiRecord {
  id: string;
  notification_type: 'SOS_ALERT' | 'CASE_UPDATE' | 'INCIDENT_FLAGGED' | 'ESCALATION' | 'SYSTEM';
  title: string;
  body: string;
  is_read: boolean;
  created_at: string;
}

export interface EvidenceCustodyReport {
  evidence_id: string;
  file_hash: string;
  chain_of_custody_valid: boolean;
  bsa_section_63_compliant: boolean;
  verified_at: string;
  tamper_detected: boolean;
}

export interface MissingChildApiRecord {
  id: string;
  child_name?: string;
  description: string;
  age_when_missing?: number;
  age?: number;
  status: string;
  last_known_address?: string;
  lastKnownLocation?: {
    lat: number;
    lng: number;
    address: string;
  };
  lastSeenAt?: string;
  reportedAt?: string;
  cctvCandidates?: any[];
  sightings?: any[];
}

export interface LongitudinalPatternsReport {
  child_id: string;
  risk_trajectory: 'ESCALATING_CRITICAL' | 'ELEVATED_CONCERN' | 'STABLE';
  detected_patterns: Array<{
    pattern_code: string;
    title: string;
    description: string;
    statutory_reference: string;
  }>;
}


export interface CopilotCaseSummaryResponse {
  case_id: string;
  protected_case_id: string;
  case_title: string;
  case_priority: string;
  case_status: string;
  child_protected_id: string;
  is_domestic_safety_mode: boolean;
  executive_summary: string;
  chronological_milestones: Array<{
    timestamp: string;
    event_type: string;
    description: string;
    severity: string;
  }>;
  suspect_profiles: any[];
  applicable_statutory_provisions: Array<{
    statute_name: string;
    section: string;
    title: string;
    relevance_summary: string;
    mandatory_reporting: boolean;
    reporting_timeline_hours?: number;
    reporting_authority?: string;
  }>;
  recommended_action_plan: string[];
  risk_assessment?: {
    composite_risk_score: number;
    threat_tier: string;
    velocity_score: number;
    severity_score: number;
    predator_persistence_score: number;
    vulnerability_score: number;
  };
  generated_by?: string;
  generated_at?: string;
}

export interface GraphDataResponse {
  case_id: string;
  nodes: Array<{
    id: string;
    label: string;
    type: 'child' | 'incident' | 'suspect' | 'location' | 'evidence' | 'platform';
    properties?: Record<string, any>;
  }>;
  edges: Array<{
    source: string;
    target: string;
    relationship: string;
    weight?: number;
  }>;
}

export interface RiskEvaluationResponse {
  entity_id: string;
  entity_type: string;
  composite_risk_score: number;
  threat_tier: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  metrics: {
    incident_velocity: number;
    severity_weighted: number;
    predator_persistence: number;
    child_vulnerability: number;
  };
  key_risk_drivers: string[];
  recommended_tier: string;
}

// ===== API SERVICE FUNCTIONS =====

export const authApi = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    const res = await api.post<LoginResponse>('/api/v1/auth/login', { email, password });
    return res.data;
  },

  register: async (data: any) => {
    const res = await api.post('/api/v1/auth/register', data);
    return res.data;
  },

  refreshToken: async (refreshToken: string) => {
    const res = await api.post('/api/v1/auth/refresh', { refresh_token: refreshToken });
    return res.data;
  },

  getMe: async () => {
    const res = await api.get('/api/v1/auth/me');
    return res.data;
  },

  updateMe: async (data: any) => {
    const res = await api.put('/api/v1/auth/me', data);
    return res.data;
  },

  reverseGeocode: async (lat: number, lon: number) => {
    const res = await api.get('/api/v1/auth/reverse-geocode', { params: { lat, lon } });
    return res.data;
  },

  logout: async (refreshToken: string) => {
    const res = await api.post('/api/v1/auth/logout', { refresh_token: refreshToken });
    return res.data;
  },
};

export const casesApi = {
  getCases: async (params?: { status?: string; priority?: string; risk_level?: string; assigned_to_me?: boolean; child_id?: string; skip?: number; limit?: number; offset?: number }) => {
    const res = await api.get<CaseApiRecord[]>('/api/v1/cases/', { params });
    return res.data;
  },

  getCaseDetail: async (id: string) => {
    const res = await api.get<CaseApiRecord>(`/api/v1/cases/${id}`);
    return res.data;
  },

  createCase: async (data: { child_id: string; title: string; description: string; priority: string; risk_level?: string }) => {
    const res = await api.post<CaseApiRecord>('/api/v1/cases/', data);
    return res.data;
  },

  updateCase: async (id: string, data: any) => {
    const res = await api.put<CaseApiRecord>(`/api/v1/cases/${id}`, data);
    return res.data;
  },

  addNote: async (id: string, note: { note_type?: 'observation' | 'action' | 'escalation'; content?: string; note?: string } | string) => {
    const payload = typeof note === 'string' ? { note } : note;
    const res = await api.post(`/api/v1/cases/${id}/notes`, payload);
    return res.data;
  },

  getNotes: async (id: string) => {
    const res = await api.get(`/api/v1/cases/${id}/notes`);
    return res.data;
  },

  escalate: async (id: string, data: { reason: string; target_authority?: string; escalate_to?: string }) => {
    const payload = {
      reason: data.reason,
      escalate_to: data.escalate_to || 'authority',
      target_authority: data.target_authority || 'authority',
    };
    const res = await api.post(`/api/v1/cases/${id}/escalate`, payload);
    return res.data;
  },

  transitionStatus: async (
    id: string,
    data: {
      to_status: string;
      reason?: string;
      statutory_reference?: string;
      dismissal_category?: string;
    }
  ) => {
    const res = await api.post(`/api/v1/cases/${id}/transition`, data);
    return res.data;
  },

  checkSla: async () => {
    const res = await api.post('/api/v1/cases/check-sla');
    return res.data;
  },
};

export const copilotApi = {
  summarizeCase: async (caseId: string): Promise<CopilotCaseSummaryResponse> => {
    try {
      const res = await api.post<CopilotCaseSummaryResponse>(`/api/v1/copilot/summarize-case/${caseId}`);
      return res.data;
    } catch (e) {
      const res = await api.post<CopilotCaseSummaryResponse>(`/api/v1/copilot/cases/${caseId}/summary`);
      return res.data;
    }
  },

  statutoryQuery: async (query: { query_text: string; incident_type?: string; child_state?: string; child_district?: string; act_filter?: string }) => {
    const res = await api.post('/api/v1/copilot/statutory-query', query);
    return res.data;
  },

  childSafetyChat: async (request: { child_id?: string; message: string; history?: any[] }) => {
    const res = await api.post('/api/v1/copilot/child-safety-chat', request);
    return res.data;
  },
};

export const securityAuditApi = {
  verifyChain: async () => {
    try {
      const res = await api.get('/api/v1/security/audit/verify-chain');
      return res.data;
    } catch (e) {
      const res = await api.get('/api/v1/security/audit/verify');
      return res.data;
    }
  },

  verifyLedger: async () => {
    try {
      const res = await api.get('/api/v1/security/audit/verify-chain');
      return res.data;
    } catch (e) {
      const res = await api.get('/api/v1/security/audit/verify');
      return res.data;
    }
  },
};

export const securityVaultApi = {
  getMaskedChild: async (childId: string) => {
    try {
      const res = await api.get(`/api/v1/security/vault/masked/${childId}`);
      return res.data;
    } catch (e) {
      const res = await api.get(`/api/v1/security/vault/${childId}/masked`);
      return res.data;
    }
  },

  resolvePII: async (childId: string, data: { legal_order_reference?: string; justification?: string; fir_number?: string; reason?: string; legal_authorization_id?: string; jurisdiction?: string }) => {
    const payload = {
      child_id: childId,
      reason: data.reason || data.justification || 'Authorized unmasking request',
      legal_authorization_id: data.legal_authorization_id || data.legal_order_reference || data.fir_number || 'FIR-UNMASK-001',
      jurisdiction: data.jurisdiction || 'Jurisdiction Authority',
      legal_order_reference: data.legal_order_reference || data.legal_authorization_id,
      justification: data.justification || data.reason,
    };
    try {
      const res = await api.post('/api/v1/security/vault/resolve', payload);
      return res.data;
    } catch (e) {
      const res = await api.post(`/api/v1/security/vault/${childId}/resolve`, payload);
      return res.data;
    }
  },
};

export const graphApi = {
  getCaseGraph: async (caseId: string): Promise<GraphDataResponse> => {
    const res = await api.get<GraphDataResponse>(`/api/v1/graph/case/${caseId}`);
    return res.data;
  },

  connectTheDots: async (params?: { case_id?: string; jurisdiction?: string; identifier?: string } | string) => {
    const queryParams = typeof params === 'string' ? { identifier: params } : params;
    const res = await api.get('/api/v1/graph/connect-the-dots', { params: queryParams });
    return res.data;
  },

  getClusters: async () => {
    const res = await api.get('/api/v1/graph/clusters');
    return res.data;
  },

  getStats: async () => {
    const res = await api.get('/api/v1/graph/stats');
    return res.data;
  },

  linkSuspect: async (req: { incident_id: string; suspect_handle: string; platform: string; modus_operandi?: string }) => {
    const res = await api.post('/api/v1/graph/link-suspect', req);
    return res.data;
  },
};

export const riskApi = {
  evaluateCaseRisk: async (caseId: string): Promise<RiskEvaluationResponse> => {
    const res = await api.get<RiskEvaluationResponse>(`/api/v1/risk/case/${caseId}`);
    return res.data;
  },

  evaluateChildRisk: async (childId: string): Promise<RiskEvaluationResponse> => {
    const res = await api.get<RiskEvaluationResponse>(`/api/v1/risk/child/${childId}`);
    return res.data;
  },

  findSimilarCases: async (caseId: string, topK = 5) => {
    const res = await api.post(`/api/v1/risk/case/${caseId}/similar`, null, { params: { top_k: topK } });
    return res.data;
  },
};

export const sosApi = {
  getActive: async (limit = 50) => {
    const res = await api.get<SosApiRecord[]>('/api/v1/sos/active', { params: { limit } });
    return res.data;
  },

  getNearby: async (lat: number, lng: number, radiusKm = 10.0) => {
    const res = await api.get<SosApiRecord[]>('/api/v1/sos/nearby', {
      params: { latitude: lat, longitude: lng, radius_km: radiusKm },
    });
    return res.data;
  },

  getDetail: async (id: string) => {
    const res = await api.get<SosApiRecord>(`/api/v1/sos/${id}`);
    return res.data;
  },

  trigger: async (data: {
    latitude: number;
    longitude: number;
    accuracy?: number;
    location_address?: string;
    message?: string;
    child_id?: string;
    is_silent_duress?: boolean;
    bypass_primary_guardians?: boolean;
  }) => {
    const res = await api.post<SosApiRecord>('/api/v1/sos/trigger', data);
    return res.data;
  },

  resolve: async (id: string, message?: string) => {
    try {
      const res = await api.post<SosApiRecord>(`/api/v1/sos/${id}/resolve`, { resolution_notes: message || 'Resolved by responder' });
      return res.data;
    } catch (e) {
      const res = await api.put<SosApiRecord>(`/api/v1/sos/${id}/resolve`, { message });
      return res.data;
    }
  },
};

export const incidentsApi = {
  getActive: async (limit = 50) => {
    const res = await api.get<IncidentApiRecord[]>('/api/v1/incidents/active', { params: { limit } });
    return res.data;
  },

  getDetail: async (id: string) => {
    const res = await api.get<IncidentApiRecord>(`/api/v1/incidents/${id}`);
    return res.data;
  },

  create: async (data: {
    case_id: string;
    incident_type: string;
    severity: string;
    description: string;
    occurred_at?: string;
  }) => {
    const res = await api.post<IncidentApiRecord>('/api/v1/incidents/', data);
    return res.data;
  },

  verify: async (id: string, trustLevel = 'moderator_verified') => {
    const res = await api.put<IncidentApiRecord>(`/api/v1/incidents/${id}/verify`, null, {
      params: { trust_level: trustLevel },
    });
    return res.data;
  },
};

export const chatApi = {
  getMessages: async (caseId: string, limit = 50, offset = 0) => {
    try {
      const res = await api.get(`/api/v1/chat/cases/${caseId}`, {
        params: { limit, offset },
      });
      return res.data;
    } catch (e) {
      const res = await api.get(`/api/v1/chat/cases/${caseId}/messages`, {
        params: { limit, offset },
      });
      return res.data;
    }
  },

  sendMessage: async (caseId: string, content: string, messageType = 'text') => {
    try {
      const res = await api.post(`/api/v1/chat/cases/${caseId}/send`, {
        content,
        message_type: messageType,
      });
      return res.data;
    } catch (e) {
      const res = await api.post(`/api/v1/chat/cases/${caseId}/messages`, {
        content,
        message_type: messageType,
      });
      return res.data;
    }
  },

  markRead: async (caseId: string) => {
    try {
      const res = await api.post(`/api/v1/chat/cases/${caseId}/read`);
      return res.data;
    } catch (e) {
      const res = await api.put(`/api/v1/chat/cases/${caseId}/read`);
      return res.data;
    }
  },
};

export const missingChildrenApi = {
  fileAlert: async (data: any) => {
    const res = await api.post('/api/v1/missing-children/', data);
    return res.data;
  },

  listAlerts: async (params?: { state?: string; district?: string; limit?: number }) => {
    const res = await api.get('/api/v1/missing-children/', { params });
    return res.data;
  },

  getDetail: async (id: string) => {
    const res = await api.get(`/api/v1/missing-children/${id}`);
    return res.data;
  },

  submitSighting: async (id: string, data: { location_address: string; sighting_notes: string; image_url?: string }) => {
    const res = await api.post(`/api/v1/missing-children/${id}/sightings`, data);
    return res.data;
  },

  verifySighting: async (sightingId: string, data: { is_match: boolean; notes: string }) => {
    const res = await api.put(`/api/v1/missing-children/sightings/${sightingId}/verify`, data);
    return res.data;
  },

  resolveMissing: async (id: string, data: { resolution_notes: string }) => {
    const res = await api.put(`/api/v1/missing-children/${id}/resolve`, data);
    return res.data;
  },
};

export const intelligenceApi = {
  getTimeline: async (childId: string) => {
    const res = await api.get(`/api/v1/intelligence/child/${childId}/timeline`);
    return res.data;
  },

  getPatterns: async (childId: string) => {
    const res = await api.get(`/api/v1/intelligence/child/${childId}/patterns`);
    return res.data;
  },

  getReport: async (childId: string) => {
    const res = await api.get(`/api/v1/intelligence/child/${childId}/report`);
    return res.data;
  },
};

export const dpdpApi = {
  getRights: async () => {
    const res = await api.get('/api/v1/dpdp/rights');
    return res.data;
  },

  requestErasure: async (reason: string, scope = 'ALL_SURVEILLANCE_AND_TRACKING') => {
    const res = await api.post('/api/v1/dpdp/erasure-request', { reason, scope });
    return res.data;
  },

  runTransitions: async () => {
    const res = await api.post('/api/v1/dpdp/run-transitions');
    return res.data;
  },

  runRetentionSweep: async () => {
    const res = await api.post('/api/v1/dpdp/run-retention-sweep');
    return res.data;
  },
};

export const reportsApi = {
  getReports: async (limit = 50, offset = 0) => {
    const res = await api.get<ReportApiRecord[]>('/api/v1/reports/', { params: { limit, offset } });
    return res.data;
  },

  getDetail: async (id: string) => {
    const res = await api.get<ReportApiRecord>(`/api/v1/reports/${id}`);
    return res.data;
  },

  submit: async (data: {
    category: string;
    content: string;
    details?: string;
    child_id?: string;
    contact_info?: string;
    is_anonymous: boolean;
  }) => {
    const res = await api.post<ReportApiRecord>('/api/v1/reports/', data);
    return res.data;
  },
};

export const notificationsApi = {
  getNotifications: async (limit = 50) => {
    const res = await api.get<{ items: NotificationApiRecord[]; unread_count: number }>('/api/v1/notifications/', {
      params: { limit },
    });
    return res.data;
  },

  markRead: async (id: string) => {
    const res = await api.put(`/api/v1/notifications/${id}/read`);
    return res.data;
  },

  markAllRead: async () => {
    const res = await api.put<{ message: string; updated_count: number }>('/api/v1/notifications/read-all');
    return res.data;
  },
};

export const evidenceApi = {
  upload: async (file: File, incidentId?: string, reportId?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (incidentId) formData.append('incident_id', incidentId);
    if (reportId) formData.append('report_id', reportId);

    const res = await api.post('/api/v1/evidence/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  verifyCustody: async (id: string): Promise<EvidenceCustodyReport> => {
    const res = await api.get<EvidenceCustodyReport>(`/api/v1/evidence/${id}/verify-custody`);
    return res.data;
  },
};

export const childrenApi = {
  listChildren: async (params?: { limit?: number; offset?: number }) => {
    const res = await api.get('/api/v1/children', { params });
    return res.data;
  },

  getChild: async (id: string) => {
    const res = await api.get(`/api/v1/children/${id}`);
    return res.data;
  },

  getTrustedAdults: async (childId: string) => {
    const res = await api.get(`/api/v1/children/${childId}/trusted-adults`);
    return res.data;
  },

  reviewNomination: async (childId: string, linkId: string, data: { approved: boolean; vetting_notes: string }) => {
    const res = await api.put(`/api/v1/children/${childId}/nominate-adult/${linkId}/review`, data);
    return res.data;
  },
};

export const healthApi = {
  check: async () => {
    const res = await api.get<{ status: string; message: string }>('/');
    return res.data;
  },

  detailedHealth: async () => {
    const res = await api.get('/api/v1/health/');
    return res.data;
  },
};
