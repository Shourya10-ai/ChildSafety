import {
  User, ProtectedChild, CaseRecord, TimelineEvent, AIFlag,
  ModeratorNote, Evidence, MissingChild, ChatMessage, Notification,
  DashboardStats, RiskTrendDataPoint, GraphNode, GraphEdge
} from '@/types';

// ===== USERS =====
export const mockUsers: User[] = [
  {
    id: 'M1042',
    name: 'Dr. Priya Sharma',
    email: 'priya.sharma@childsafety.org',
    role: 'moderator',
    department: 'Child Welfare',
    assignedChildren: 12,
  },
  {
    id: 'A2001',
    name: 'Inspector Rajesh Kapoor',
    email: 'r.kapoor@authority.gov.in',
    role: 'authority',
    department: 'Cyber Crime Division',
  },
];

// ===== PROTECTED CHILDREN =====
export const mockChildren: ProtectedChild[] = [
  { id: '#C8291', age: 13, riskLevel: 'high', assignedModeratorId: 'M1042', activeCases: 2, totalIncidents: 7, lastActivity: '2026-09-12T05:30:00Z', riskTrend: 'increasing', status: 'active' },
  { id: '#C4512', age: 11, riskLevel: 'medium', assignedModeratorId: 'M1042', activeCases: 1, totalIncidents: 3, lastActivity: '2026-09-11T14:20:00Z', riskTrend: 'stable', status: 'active' },
  { id: '#C7720', age: 15, riskLevel: 'critical', assignedModeratorId: 'M1042', activeCases: 3, totalIncidents: 12, lastActivity: '2026-09-12T06:00:00Z', riskTrend: 'increasing', status: 'active' },
  { id: '#C3301', age: 9, riskLevel: 'low', assignedModeratorId: 'M1042', activeCases: 0, totalIncidents: 1, lastActivity: '2026-09-10T10:00:00Z', riskTrend: 'decreasing', status: 'monitoring' },
  { id: '#C5589', age: 14, riskLevel: 'medium', assignedModeratorId: 'M1042', activeCases: 1, totalIncidents: 4, lastActivity: '2026-09-11T18:45:00Z', riskTrend: 'stable', status: 'active' },
  { id: '#C9102', age: 12, riskLevel: 'high', assignedModeratorId: 'M1042', activeCases: 2, totalIncidents: 6, lastActivity: '2026-09-12T03:15:00Z', riskTrend: 'increasing', status: 'active' },
  { id: '#C1147', age: 16, riskLevel: 'low', assignedModeratorId: 'M1042', activeCases: 0, totalIncidents: 2, lastActivity: '2026-09-09T12:00:00Z', riskTrend: 'decreasing', status: 'resolved' },
  { id: '#C6633', age: 10, riskLevel: 'medium', assignedModeratorId: 'M1042', activeCases: 1, totalIncidents: 3, lastActivity: '2026-09-11T20:30:00Z', riskTrend: 'stable', status: 'active' },
  { id: '#C2205', age: 13, riskLevel: 'high', assignedModeratorId: 'M1042', activeCases: 2, totalIncidents: 8, lastActivity: '2026-09-12T04:00:00Z', riskTrend: 'increasing', status: 'active' },
  { id: '#C8874', age: 11, riskLevel: 'low', assignedModeratorId: 'M1042', activeCases: 0, totalIncidents: 1, lastActivity: '2026-09-08T09:00:00Z', riskTrend: 'stable', status: 'monitoring' },
  { id: '#C4401', age: 14, riskLevel: 'critical', assignedModeratorId: 'M1042', activeCases: 3, totalIncidents: 15, lastActivity: '2026-09-12T06:30:00Z', riskTrend: 'increasing', status: 'active' },
  { id: '#C7790', age: 8, riskLevel: 'medium', assignedModeratorId: 'M1042', activeCases: 1, totalIncidents: 2, lastActivity: '2026-09-11T16:00:00Z', riskTrend: 'stable', status: 'active' },
];

// ===== CASES =====
export const mockCases: CaseRecord[] = [
  { id: 'CASE-001', childId: '#C8291', status: 'active', riskLevel: 'high', createdAt: '2026-08-15T10:00:00Z', updatedAt: '2026-09-12T05:30:00Z', assignedModeratorId: 'M1042', incidentCount: 5, description: 'Repeated online harassment and cyberbullying detected across multiple platforms.', tags: ['cyberbullying', 'harassment'] },
  { id: 'CASE-002', childId: '#C7720', status: 'escalated', riskLevel: 'critical', createdAt: '2026-07-20T08:00:00Z', updatedAt: '2026-09-12T06:00:00Z', assignedModeratorId: 'M1042', incidentCount: 9, description: 'Suspected grooming pattern detected. Multiple AI flags confirmed by moderator. Case escalated to authorities.', tags: ['grooming', 'threat'] },
  { id: 'CASE-003', childId: '#C4512', status: 'under_review', riskLevel: 'medium', createdAt: '2026-09-01T12:00:00Z', updatedAt: '2026-09-11T14:20:00Z', assignedModeratorId: 'M1042', incidentCount: 3, description: 'Child reported bullying incidents at school. AI detected related online harassment.', tags: ['bullying', 'cyberbullying'] },
  { id: 'CASE-004', childId: '#C4401', status: 'escalated', riskLevel: 'critical', createdAt: '2026-06-10T09:00:00Z', updatedAt: '2026-09-12T06:30:00Z', assignedModeratorId: 'M1042', incidentCount: 12, description: 'Complex case involving multiple threat indicators and cross-platform harassment. Knowledge graph reveals connections to other cases.', tags: ['threat', 'harassment', 'grooming'] },
  { id: 'CASE-005', childId: '#C9102', status: 'active', riskLevel: 'high', createdAt: '2026-08-25T15:00:00Z', updatedAt: '2026-09-12T03:15:00Z', assignedModeratorId: 'M1042', incidentCount: 4, description: 'SOS triggered twice. Child reports feeling unsafe. Counselling referral initiated.', tags: ['sos', 'abuse'] },
  { id: 'CASE-006', childId: '#C5589', status: 'active', riskLevel: 'medium', createdAt: '2026-09-05T11:00:00Z', updatedAt: '2026-09-11T18:45:00Z', assignedModeratorId: 'M1042', incidentCount: 2, description: 'AI flagged potential inappropriate content targeting. Under moderator review.', tags: ['cyberbullying'] },
  { id: 'CASE-007', childId: '#C2205', status: 'active', riskLevel: 'high', createdAt: '2026-08-01T07:00:00Z', updatedAt: '2026-09-12T04:00:00Z', assignedModeratorId: 'M1042', incidentCount: 6, description: 'Persistent targeted harassment from identified accounts. Evidence collected and verified.', tags: ['harassment', 'threat'] },
  { id: 'CASE-008', childId: '#C3301', status: 'resolved', riskLevel: 'low', createdAt: '2026-08-20T13:00:00Z', updatedAt: '2026-09-10T10:00:00Z', assignedModeratorId: 'M1042', incidentCount: 1, description: 'Single bullying incident reported and resolved through school coordination.', tags: ['bullying'] },
];

// ===== TIMELINE EVENTS =====
export const mockTimeline: TimelineEvent[] = [
  { id: 'TL-001', caseId: 'CASE-001', type: 'report', trustLevel: 'raw', title: 'Anonymous Report Submitted', description: 'Child reported repeated insults and threats from an online account.', timestamp: '2026-08-15T10:00:00Z', source: 'Child #C8291' },
  { id: 'TL-002', caseId: 'CASE-001', type: 'ai_flag', trustLevel: 'ai_derived', title: 'AI: Cyberbullying Detected', description: 'NLP model detected cyberbullying with 89% confidence. Language: Hinglish (code-mixed).', timestamp: '2026-08-15T10:05:00Z', source: 'Safety NLP Pipeline', metadata: { confidence: 0.89, model: 'XLM-R-v2' } },
  { id: 'TL-003', caseId: 'CASE-001', type: 'moderator_note', trustLevel: 'human_verified', title: 'Moderator Assessment', description: 'Confirmed bullying. Child appears distressed. Recommended: follow-up within 48 hours. Counselling referral initiated.', timestamp: '2026-08-15T14:30:00Z', source: 'Dr. Priya Sharma (M1042)' },
  { id: 'TL-004', caseId: 'CASE-001', type: 'communication', trustLevel: 'human_verified', title: 'Moderator ↔ Child Communication', description: 'Moderator established contact. Child shared additional details about the harassment pattern.', timestamp: '2026-08-17T09:00:00Z', source: 'Communication Channel' },
  { id: 'TL-005', caseId: 'CASE-001', type: 'ai_flag', trustLevel: 'ai_derived', title: 'AI: Threat Detected', description: 'Threat classifier detected threatening message with 76% confidence. Severity: moderate.', timestamp: '2026-08-20T16:00:00Z', source: 'Threat Detection Pipeline', metadata: { confidence: 0.76 } },
  { id: 'TL-006', caseId: 'CASE-001', type: 'evidence', trustLevel: 'human_verified', title: 'Evidence Verified', description: 'Screenshot evidence verified by moderator. Hash recorded. Threat confirmed.', timestamp: '2026-08-21T10:00:00Z', source: 'Dr. Priya Sharma (M1042)' },
  { id: 'TL-007', caseId: 'CASE-001', type: 'moderator_note', trustLevel: 'human_verified', title: 'Follow-up Assessment', description: 'Harassment pattern continuing. Risk level elevated to HIGH. Recommending enhanced monitoring.', timestamp: '2026-09-01T11:00:00Z', source: 'Dr. Priya Sharma (M1042)' },
  { id: 'TL-008', caseId: 'CASE-001', type: 'status_change', trustLevel: 'human_verified', title: 'Risk Level Updated', description: 'Risk level changed from MEDIUM to HIGH based on incident frequency and severity trend.', timestamp: '2026-09-05T14:00:00Z', source: 'Risk Engine + Moderator Verification' },
];

// ===== AI FLAGS =====
export const mockFlags: AIFlag[] = [
  { id: 'FL-001', childId: '#C8291', caseId: 'CASE-001', type: 'bullying', confidence: 0.89, riskLevel: 'high', contentSnippet: '"tu bahut kamzor hai... koi tujhe pasand nahi karta" [Translated: You are very weak... nobody likes you]', detectedAt: '2026-09-12T04:30:00Z', status: 'pending', language: 'Hinglish' },
  { id: 'FL-002', childId: '#C7720', caseId: 'CASE-002', type: 'grooming', confidence: 0.92, riskLevel: 'critical', contentSnippet: 'Pattern: age-inappropriate relationship building, isolation attempts, secrecy requests detected across 14 messages.', detectedAt: '2026-09-12T05:15:00Z', status: 'pending', language: 'English' },
  { id: 'FL-003', childId: '#C9102', caseId: 'CASE-005', type: 'threat', confidence: 0.76, riskLevel: 'high', contentSnippet: '"agar kisiko bataya toh..." [Translated: If you tell anyone then...]', detectedAt: '2026-09-12T03:00:00Z', status: 'pending', language: 'Hindi' },
  { id: 'FL-004', childId: '#C5589', caseId: 'CASE-006', type: 'harassment', confidence: 0.71, riskLevel: 'medium', contentSnippet: 'Repeated targeted messaging pattern detected. 23 messages in 48 hours from same account.', detectedAt: '2026-09-11T18:00:00Z', status: 'pending', language: 'English' },
  { id: 'FL-005', childId: '#C4401', caseId: 'CASE-004', type: 'grooming', confidence: 0.88, riskLevel: 'critical', contentSnippet: 'Account shows predatory behavioral pattern: gift promises, secrecy enforcement, platform migration attempts.', detectedAt: '2026-09-12T06:00:00Z', status: 'confirmed', moderatorFeedback: 'Confirmed. Pattern is consistent with grooming stages 3-4.', language: 'English + Hindi' },
  { id: 'FL-006', childId: '#C2205', caseId: 'CASE-007', type: 'threat', confidence: 0.83, riskLevel: 'high', contentSnippet: 'Direct threats of physical harm detected in voice message transcript.', detectedAt: '2026-09-11T22:00:00Z', status: 'pending', language: 'Hindi' },
  { id: 'FL-007', childId: '#C6633', caseId: 'CASE-003', type: 'bullying', confidence: 0.65, riskLevel: 'medium', contentSnippet: 'Group chat bullying pattern detected. Multiple users targeting child.', detectedAt: '2026-09-11T19:30:00Z', status: 'false_positive', moderatorFeedback: 'Reviewed — context is a gaming group with playful banter. No genuine bullying intent.', language: 'Hinglish' },
  { id: 'FL-008', childId: '#C4512', caseId: 'CASE-003', type: 'inappropriate_content', confidence: 0.74, riskLevel: 'medium', contentSnippet: 'Age-inappropriate content shared to child in private message.', detectedAt: '2026-09-11T12:00:00Z', status: 'pending', language: 'English' },
];

// ===== MODERATOR NOTES =====
export const mockNotes: ModeratorNote[] = [
  { id: 'NOTE-001', caseId: 'CASE-001', moderatorId: 'M1042', content: 'Child appears distressed during communication. Reports that harassment has been ongoing for approximately 3 weeks. The perpetrator appears to be a classmate using an anonymous account. Recommended: Follow-up within 48 hours, counselling referral.', createdAt: '2026-08-15T14:30:00Z', type: 'assessment' },
  { id: 'NOTE-002', caseId: 'CASE-001', moderatorId: 'M1042', content: 'Follow-up completed. Child reports harassment has reduced but not stopped. New evidence submitted (screenshot). Evidence verified — threat confirmed. Continuing monitoring.', createdAt: '2026-08-21T10:30:00Z', type: 'follow_up' },
  { id: 'NOTE-003', caseId: 'CASE-002', moderatorId: 'M1042', content: 'CRITICAL ASSESSMENT: Pattern strongly indicates grooming behavior at advanced stages. Multiple risk indicators confirmed. Recommend immediate escalation to authorities. Evidence package prepared.', createdAt: '2026-09-10T09:00:00Z', type: 'assessment' },
];

// ===== EVIDENCE =====
export const mockEvidence: Evidence[] = [
  { id: 'EV-001', caseId: 'CASE-001', type: 'screenshot', source: 'Child submission', capturedAt: '2026-08-15T10:00:00Z', aiAnalysis: { threatProbability: 0.12, bullyingProbability: 0.89 }, moderatorVerification: { verified: true, verifiedBy: 'M1042', verifiedAt: '2026-08-15T14:30:00Z', notes: 'Confirmed cyberbullying content.' }, trustLevel: 'human_verified', description: 'Screenshot of harassment messages in chat application' },
  { id: 'EV-002', caseId: 'CASE-001', type: 'screenshot', source: 'Child submission', capturedAt: '2026-08-20T16:00:00Z', aiAnalysis: { threatProbability: 0.76, bullyingProbability: 0.45 }, moderatorVerification: { verified: true, verifiedBy: 'M1042', verifiedAt: '2026-08-21T10:00:00Z', notes: 'Threat confirmed. Direct threatening language used.' }, trustLevel: 'human_verified', description: 'Screenshot of threatening messages' },
  { id: 'EV-003', caseId: 'CASE-002', type: 'text', source: 'AI extraction', capturedAt: '2026-09-10T08:00:00Z', aiAnalysis: { groomingProbability: 0.92 }, trustLevel: 'ai_derived', description: 'Extracted conversation pattern showing grooming indicators' },
  { id: 'EV-004', caseId: 'CASE-005', type: 'audio', source: 'Voice report', capturedAt: '2026-09-12T03:00:00Z', aiAnalysis: { threatProbability: 0.76 }, trustLevel: 'ai_derived', description: 'Voice message containing threats — transcribed via Whisper ASR' },
];

// ===== MISSING CHILDREN =====
export const mockMissingChildren: MissingChild[] = [
  {
    id: 'MC-001', caseId: 'CASE-MC-001',
    description: 'Last seen near Central Market area wearing school uniform. Carries a blue backpack.',
    age: 11, clothing: 'White school shirt, navy blue trousers, blue backpack',
    lastKnownLocation: { lat: 28.6139, lng: 77.2090, address: 'Connaught Place, New Delhi' },
    lastSeenAt: '2026-09-11T07:30:00Z', reportedAt: '2026-09-11T12:00:00Z',
    status: 'active',
    identifyingCharacteristics: ['Small scar on left hand', 'Wears glasses'],
    cctvCandidates: [
      { id: 'CCTV-001', location: { lat: 28.6145, lng: 77.2095, address: 'Rajiv Chowk Metro Station' }, capturedAt: '2026-09-11T08:15:00Z', similarityScore: 0.87, verified: false, cameraId: 'CAM-RC-04' },
      { id: 'CCTV-002', location: { lat: 28.6200, lng: 77.2150, address: 'Mandi House Junction' }, capturedAt: '2026-09-11T09:02:00Z', similarityScore: 0.72, verified: false, cameraId: 'CAM-MH-12' },
    ]
  },
  {
    id: 'MC-002', caseId: 'CASE-MC-002',
    description: 'Did not return home from after-school activity. Last seen leaving school premises.',
    age: 14, clothing: 'Green kurta, jeans, white sneakers',
    lastKnownLocation: { lat: 19.0760, lng: 72.8777, address: 'Bandra West, Mumbai' },
    lastSeenAt: '2026-09-10T16:00:00Z', reportedAt: '2026-09-10T20:00:00Z',
    status: 'investigating',
    identifyingCharacteristics: ['Tall for age', 'Short hair'],
    cctvCandidates: [
      { id: 'CCTV-003', location: { lat: 19.0780, lng: 72.8790, address: 'Bandra Station West' }, capturedAt: '2026-09-10T16:45:00Z', similarityScore: 0.81, verified: false, cameraId: 'CAM-BW-07' },
    ]
  },
];

// ===== GRAPH DATA =====
export const mockGraphNodes: GraphNode[] = [
  { id: 'n1', type: 'child', label: '#C8291', metadata: { riskLevel: 'high' } },
  { id: 'n2', type: 'child', label: '#C7720', metadata: { riskLevel: 'critical' } },
  { id: 'n3', type: 'child', label: '#C4401', metadata: { riskLevel: 'critical' } },
  { id: 'n4', type: 'incident', label: 'Cyberbullying #1', metadata: { type: 'cyberbullying' } },
  { id: 'n5', type: 'incident', label: 'Grooming #1', metadata: { type: 'grooming' } },
  { id: 'n6', type: 'incident', label: 'Threat #1', metadata: { type: 'threat' } },
  { id: 'n7', type: 'account', label: 'Account @anon_x42', metadata: {} },
  { id: 'n8', type: 'account', label: 'Account @helper_friend', metadata: {} },
  { id: 'n9', type: 'location', label: 'Delhi NCR', metadata: { lat: 28.6139, lng: 77.2090 } },
  { id: 'n10', type: 'location', label: 'Mumbai West', metadata: { lat: 19.0760, lng: 72.8777 } },
  { id: 'n11', type: 'evidence', label: 'Evidence #EV-001', metadata: {} },
  { id: 'n12', type: 'evidence', label: 'Evidence #EV-003', metadata: {} },
];

export const mockGraphEdges: GraphEdge[] = [
  { source: 'n1', target: 'n4', relationship: 'reported' },
  { source: 'n4', target: 'n7', relationship: 'involves_account' },
  { source: 'n2', target: 'n5', relationship: 'reported' },
  { source: 'n5', target: 'n8', relationship: 'involves_account' },
  { source: 'n3', target: 'n6', relationship: 'reported' },
  { source: 'n6', target: 'n7', relationship: 'involves_account' }, // Same account as n1's incident!
  { source: 'n6', target: 'n8', relationship: 'involves_account' }, // Same account as n2's incident!
  { source: 'n4', target: 'n9', relationship: 'occurred_at' },
  { source: 'n5', target: 'n9', relationship: 'occurred_at' },
  { source: 'n6', target: 'n10', relationship: 'occurred_at' },
  { source: 'n4', target: 'n11', relationship: 'has_evidence' },
  { source: 'n5', target: 'n12', relationship: 'has_evidence' },
];

// ===== CHAT MESSAGES =====
export const mockChatMessages: Record<string, ChatMessage[]> = {
  '#C8291': [
    { id: 'MSG-001', senderId: '#C8291', senderRole: 'child', content: 'Someone keeps sending me mean messages. I dont know what to do.', timestamp: '2026-09-11T10:00:00Z', read: true },
    { id: 'MSG-002', senderId: 'M1042', senderRole: 'moderator', content: 'Thank you for reaching out. You are safe here. Can you tell me more about what kind of messages you are receiving?', timestamp: '2026-09-11T10:15:00Z', read: true },
    { id: 'MSG-003', senderId: '#C8291', senderRole: 'child', content: 'They say bad things about me and tell others to not talk to me. Its been happening for weeks.', timestamp: '2026-09-11T10:20:00Z', read: true },
    { id: 'MSG-004', senderId: 'M1042', senderRole: 'moderator', content: 'I understand, and I want you to know that this is not your fault. We are going to help you with this. Can you share any screenshots safely?', timestamp: '2026-09-11T10:30:00Z', read: true },
    { id: 'MSG-005', senderId: '#C8291', senderRole: 'child', content: 'Yes I took some screenshots. Sending them now.', timestamp: '2026-09-11T10:35:00Z', read: true },
    { id: 'MSG-006', senderId: 'M1042', senderRole: 'moderator', content: 'Thank you for sharing those. I have reviewed them and recorded them as evidence. We will take appropriate steps. Is there anything else you want to share?', timestamp: '2026-09-11T11:00:00Z', read: false },
  ],
};

// ===== NOTIFICATIONS =====
export const mockNotifications: Notification[] = [
  { id: 'NOTIF-001', type: 'ai_flag', title: 'New AI Flag: Grooming Detected', description: 'Critical grooming pattern detected for Child #C7720. 92% confidence.', timestamp: '2026-09-12T05:15:00Z', read: false, priority: 'urgent', actionUrl: '/moderator/flags' },
  { id: 'NOTIF-002', type: 'sos', title: 'SOS Alert: Child #C9102', description: 'Emergency SOS triggered. Location captured.', timestamp: '2026-09-12T03:00:00Z', read: false, priority: 'urgent', actionUrl: '/moderator/cases/CASE-005' },
  { id: 'NOTIF-003', type: 'ai_flag', title: 'New AI Flag: Bullying', description: 'Cyberbullying detected for Child #C8291. 89% confidence.', timestamp: '2026-09-12T04:30:00Z', read: false, priority: 'high', actionUrl: '/moderator/flags' },
  { id: 'NOTIF-004', type: 'message', title: 'New message from Child #C8291', description: 'Child has sent a new message in the communication channel.', timestamp: '2026-09-11T10:35:00Z', read: true, priority: 'medium', actionUrl: '/moderator/chat' },
  { id: 'NOTIF-005', type: 'case_update', title: 'Case CASE-002 Escalated', description: 'Case has been escalated to authority portal.', timestamp: '2026-09-10T09:30:00Z', read: true, priority: 'high', actionUrl: '/moderator/cases/CASE-002' },
  { id: 'NOTIF-006', type: 'escalation', title: 'New Escalated Case', description: 'Case CASE-004 escalated to authority review. Critical risk level.', timestamp: '2026-09-12T06:30:00Z', read: false, priority: 'urgent', actionUrl: '/authority/cases' },
];

// ===== DASHBOARD STATS =====
export const mockModeratorStats: DashboardStats = {
  activeCases: 6,
  activeCasesDelta: 2,
  newFlags: 8,
  newFlagsDelta: 3,
  urgentCases: 3,
  urgentCasesDelta: 1,
  assignedChildren: 12,
  assignedChildrenDelta: 0,
  resolvedThisWeek: 2,
  resolvedDelta: 1,
  escalatedCases: 2,
  escalatedDelta: 1,
};

export const mockAuthorityStats: DashboardStats = {
  activeCases: 4,
  activeCasesDelta: 1,
  newFlags: 5,
  newFlagsDelta: 2,
  urgentCases: 2,
  urgentCasesDelta: 0,
  assignedChildren: 0,
  assignedChildrenDelta: 0,
  resolvedThisWeek: 1,
  resolvedDelta: 0,
  escalatedCases: 4,
  escalatedDelta: 2,
  missingChildren: 2,
  missingChildrenDelta: 1,
  activeInvestigations: 3,
  activeInvestigationsDelta: 1,
};

// ===== RISK TREND DATA =====
export const mockRiskTrend: RiskTrendDataPoint[] = [
  { date: '2026-07-01', riskScore: 25, incidents: 1 },
  { date: '2026-07-15', riskScore: 30, incidents: 1 },
  { date: '2026-08-01', riskScore: 38, incidents: 2 },
  { date: '2026-08-15', riskScore: 52, incidents: 3 },
  { date: '2026-09-01', riskScore: 61, incidents: 4 },
  { date: '2026-09-05', riskScore: 68, incidents: 5 },
  { date: '2026-09-10', riskScore: 75, incidents: 6 },
  { date: '2026-09-12', riskScore: 82, incidents: 7 },
];

export const mockRiskTrendOverall: RiskTrendDataPoint[] = [
  { date: 'Jan', riskScore: 12, incidents: 3 },
  { date: 'Feb', riskScore: 15, incidents: 4 },
  { date: 'Mar', riskScore: 18, incidents: 5 },
  { date: 'Apr', riskScore: 22, incidents: 7 },
  { date: 'May', riskScore: 28, incidents: 9 },
  { date: 'Jun', riskScore: 35, incidents: 12 },
  { date: 'Jul', riskScore: 42, incidents: 15 },
  { date: 'Aug', riskScore: 55, incidents: 20 },
  { date: 'Sep', riskScore: 48, incidents: 18 },
];
