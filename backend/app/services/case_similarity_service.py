from __future__ import annotations
import uuid
import math
import re
from datetime import datetime
from typing import List, Dict, Set, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.case import Case, Incident
from app.models.child import Child
from app.models.knowledge_graph import SuspectEntity, IncidentSuspectLink
from app.schemas.case_similarity import (
    CaseSimilarityMatch,
    CaseSimilarityResponse
)

class CaseSimilarityService:
    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        if not text:
            return set()
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        stopwords = {
            "the", "and", "for", "with", "was", "this", "that", "from", "have", "been",
            "child", "case", "incident", "user", "report", "said", "contacted"
        }
        return set(w for w in words if w not in stopwords)

    @classmethod
    async def find_similar_cases(
        cls,
        db: AsyncSession,
        case_id: uuid.UUID,
        top_k: int = 5
    ) -> CaseSimilarityResponse:
        """
        Calculates multi-dimensional similarity between a query case and all candidate cases,
        combining Modus Operandi tactics, shared suspect handles, and spatial-temporal proximity.
        """
        # 1. Fetch Target Case
        target_stmt = select(Case).where(Case.id == case_id)
        target_case = (await db.execute(target_stmt)).scalar_one_or_none()
        if not target_case:
            raise ValueError(f"Case with ID {case_id} not found")

        # Target Child & Location
        t_child_stmt = select(Child).where(Child.id == target_case.child_id)
        target_child = (await db.execute(t_child_stmt)).scalar_one_or_none()
        target_state = target_child.state if target_child else None
        target_district = target_child.district if target_child else None

        # Target Incidents & MO
        t_inc_stmt = select(Incident).where(Incident.case_id == target_case.id)
        target_incidents = (await db.execute(t_inc_stmt)).scalars().all()
        target_types = {inc.incident_type for inc in target_incidents}
        target_text = " ".join((inc.description or "") for inc in target_incidents)
        target_tokens = cls._tokenize(f"{target_case.title or ''} {target_case.description or ''} {target_text}")

        # Target Suspects & MO
        t_inc_ids = [inc.id for inc in target_incidents]
        t_links = []
        if t_inc_ids:
            links_stmt = select(IncidentSuspectLink).where(IncidentSuspectLink.incident_id.in_(t_inc_ids))
            t_links = (await db.execute(links_stmt)).scalars().all()

        target_mo = {lk.modus_operandi for lk in t_links if lk.modus_operandi != "UNKNOWN"}
        target_suspect_ids = {lk.suspect_id for lk in t_links}

        target_suspects_map: Dict[uuid.UUID, SuspectEntity] = {}
        if target_suspect_ids:
            sus_stmt = select(SuspectEntity).where(SuspectEntity.id.in_(target_suspect_ids))
            for s in (await db.execute(sus_stmt)).scalars().all():
                target_suspects_map[s.id] = s

        target_suspect_idents = {s.identifier.lower() for s in target_suspects_map.values()}
        target_platforms = {s.platform for s in target_suspects_map.values()}

        # 2. Fetch Candidates (excluding target case itself)
        cand_stmt = select(Case).where(Case.id != target_case.id)
        candidates = (await db.execute(cand_stmt)).scalars().all()

        matches: List[CaseSimilarityMatch] = []

        for cand in candidates:
            # Candidate Child & Location
            c_child_stmt = select(Child).where(Child.id == cand.child_id)
            c_child = (await db.execute(c_child_stmt)).scalar_one_or_none()
            cand_state = c_child.state if c_child else None
            cand_district = c_child.district if c_child else None

            # Candidate Incidents
            c_inc_stmt = select(Incident).where(Incident.case_id == cand.id)
            c_incidents = (await db.execute(c_inc_stmt)).scalars().all()
            cand_types = {inc.incident_type for inc in c_incidents}
            cand_text = " ".join((inc.description or "") for inc in c_incidents)
            cand_tokens = cls._tokenize(f"{cand.title or ''} {cand.description or ''} {cand_text}")

            # Candidate Suspects & MO
            c_inc_ids = [inc.id for inc in c_incidents]
            c_links = []
            if c_inc_ids:
                c_links_stmt = select(IncidentSuspectLink).where(IncidentSuspectLink.incident_id.in_(c_inc_ids))
                c_links = (await db.execute(c_links_stmt)).scalars().all()

            cand_mo = {lk.modus_operandi for lk in c_links if lk.modus_operandi != "UNKNOWN"}
            cand_suspect_ids = {lk.suspect_id for lk in c_links}

            cand_suspects_map: Dict[uuid.UUID, SuspectEntity] = {}
            if cand_suspect_ids:
                c_sus_stmt = select(SuspectEntity).where(SuspectEntity.id.in_(cand_suspect_ids))
                for s in (await db.execute(c_sus_stmt)).scalars().all():
                    cand_suspects_map[s.id] = s

            cand_suspect_idents = {s.identifier.lower() for s in cand_suspects_map.values()}
            cand_platforms = {s.platform for s in cand_suspects_map.values()}

            # ----------------------------------------------------
            # DIMENSION 1: Modus Operandi & Keyword Similarity (Weight: 40%)
            # ----------------------------------------------------
            mo_overlap = target_mo.intersection(cand_mo)
            type_overlap = target_types.intersection(cand_types)
            token_overlap = target_tokens.intersection(cand_tokens)
            token_union = target_tokens.union(cand_tokens)

            jaccard = (len(token_overlap) / len(token_union)) if token_union else 0.0
            mo_score = 0.0
            if mo_overlap:
                mo_score += 0.5 * (len(mo_overlap) / max(len(target_mo.union(cand_mo)), 1))
            if type_overlap:
                mo_score += 0.3 * (len(type_overlap) / max(len(target_types.union(cand_types)), 1))
            mo_score += 0.2 * jaccard
            mo_score = min(mo_score, 1.0)

            # ----------------------------------------------------
            # DIMENSION 2: Suspect & Platform Overlap (Weight: 35%)
            # ----------------------------------------------------
            shared_suspects = list(target_suspect_idents.intersection(cand_suspect_idents))
            shared_platforms = list(target_platforms.intersection(cand_platforms))

            suspect_score = 0.0
            if shared_suspects:
                suspect_score = 1.0
            elif shared_platforms and mo_overlap:
                suspect_score = 0.45
            elif shared_platforms:
                suspect_score = 0.20

            # ----------------------------------------------------
            # DIMENSION 3: Spatial-Temporal Proximity (Weight: 25%)
            # ----------------------------------------------------
            same_district = bool(target_district and cand_district and target_district.lower() == cand_district.lower())
            same_state = bool(target_state and cand_state and target_state.lower() == cand_state.lower())

            spatial_score = 0.0
            if same_district:
                spatial_score = 1.0
            elif same_state:
                spatial_score = 0.5

            # Temporal delta
            t_created = target_case.created_at or datetime.utcnow()
            c_created = cand.created_at or datetime.utcnow()
            delta_days = abs((t_created - c_created).days)
            temporal_decay = math.exp(-delta_days / 60.0)  # Decay over ~60 days
            spatio_temporal_score = spatial_score * 0.7 + temporal_decay * 0.3

            # Composite Normalized Score
            composite_score = (0.40 * mo_score) + (0.35 * suspect_score) + (0.25 * spatio_temporal_score)
            composite_score = round(min(max(composite_score, 0.0), 1.0), 3)

            # Match Reasons
            reasons = []
            if shared_suspects:
                reasons.append(f"Identical suspect identifier: {', '.join(shared_suspects)}")
            if mo_overlap:
                reasons.append(f"Shared modus operandi: {', '.join(mo_overlap).replace('_', ' ').title()}")
            if same_district:
                reasons.append(f"Same jurisdictional district: {cand_district}")
            elif same_state:
                reasons.append(f"Same state: {cand_state}")
            if type_overlap:
                reasons.append(f"Similar incident category: {', '.join(type_overlap).replace('_', ' ').title()}")
            if delta_days <= 14:
                reasons.append(f"Occurred within {delta_days} days")

            if composite_score >= 0.15:
                matches.append(CaseSimilarityMatch(
                    case_id=cand.id,
                    protected_case_id=cand.protected_case_id,
                    title=cand.title,
                    status=cand.status,
                    priority=cand.priority,
                    similarity_score=composite_score,
                    common_modus_operandi=list(mo_overlap),
                    shared_suspects=shared_suspects,
                    location=f"{cand_district}, {cand_state}" if cand_district else cand_state,
                    spatial_proximity_match=same_district or same_state,
                    temporal_delta_days=delta_days,
                    match_reasons=reasons
                ))

        matches.sort(key=lambda m: m.similarity_score, reverse=True)
        top_matches = matches[:top_k]

        return CaseSimilarityResponse(
            query_case_id=target_case.id,
            query_protected_case_id=target_case.protected_case_id,
            top_matches=top_matches,
            total_candidates_analyzed=len(candidates)
        )
