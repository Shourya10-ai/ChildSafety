from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field

class SuspectEntityBase(BaseModel):
    identifier: str = Field(..., description="Suspect handle, phone number, email, or gaming tag")
    identifier_type: str = Field("SOCIAL_HANDLE", description="SOCIAL_HANDLE, PHONE_NUMBER, EMAIL, IP_ADDRESS, ONLINE_GAMING_TAG")
    platform: str = Field("OTHER", description="INSTAGRAM, TELEGRAM, WHATSAPP, DISCORD, SNAPCHAT, ROBLOX, OTHER")
    risk_level: str = Field("MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
    notes: Optional[str] = None

class SuspectEntityCreate(SuspectEntityBase):
    pass

class SuspectEntityOut(SuspectEntityBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    first_seen_at: datetime
    last_seen_at: datetime
    is_active_threat: bool
    created_at: datetime

class LinkSuspectRequest(BaseModel):
    incident_id: uuid.UUID
    identifier: str
    identifier_type: str = "SOCIAL_HANDLE"
    platform: str = "OTHER"
    modus_operandi: str = "GROOMING_GIFTING"  # GROOMING_GIFTING, SEXTORTION, COERCION_BULLYING, MEETUP_ENTICEMENT, IMPERSONATION, CYBERSTALKING
    confidence_score: float = 1.0
    details: Optional[str] = None
    risk_level: str = "MEDIUM"

class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # CHILD, CASE, INCIDENT, SUSPECT, LOCATION, INSTITUTION
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relation: str  # TARGETED_BY, INVOLVED_IN, OPERATES, OCCURRED_IN, ATTENDS, LINKED_TO
    properties: Dict[str, Any] = Field(default_factory=dict)

class GraphDataResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]

class SuspectCluster(BaseModel):
    cluster_id: str
    suspect_identifier: str
    identifier_type: str
    platform: str
    risk_level: str
    linked_cases_count: int
    victim_child_ids: List[str]
    modus_operandi_list: List[str]
    geographic_reach: List[str]
    first_seen_at: datetime
    last_seen_at: datetime

class PredatoryClustersResponse(BaseModel):
    clusters: List[SuspectCluster]
    total_clusters: int
    multi_victim_predators_count: int

class ConnectTheDotsResponse(BaseModel):
    suspect_identifier: str
    platform: str
    risk_level: str
    victim_children: List[Dict[str, Any]]
    associated_cases: List[Dict[str, Any]]
    modus_operandi: List[str]
    districts_involved: List[str]
    cross_jurisdictional: bool

class GraphStatsResponse(BaseModel):
    total_nodes: int
    total_edges: int
    suspects_count: int
    cases_count: int
    incidents_count: int
    multi_victim_predators_count: int
