from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_

from app.models.case import Case, Incident
from app.models.child import Child
from app.models.knowledge_graph import SuspectEntity, IncidentSuspectLink
from app.schemas.knowledge_graph import (
    GraphNode,
    GraphEdge,
    GraphDataResponse,
    SuspectCluster,
    PredatoryClustersResponse,
    ConnectTheDotsResponse,
    GraphStatsResponse,
    LinkSuspectRequest,
    SuspectEntityOut,
)

class KnowledgeGraphService:
    @staticmethod
    async def link_suspect_to_incident(
        db: AsyncSession,
        req: LinkSuspectRequest
    ) -> SuspectEntityOut:
        """
        Associates an online suspect handle/phone with an incident, creating or updating the suspect entity.
        """
        # 1. Verify incident exists
        stmt = select(Incident).where(Incident.id == req.incident_id)
        res = await db.execute(stmt)
        incident = res.scalar_one_or_none()
        if not incident:
            raise ValueError(f"Incident with ID {req.incident_id} not found")

        # 2. Find or create SuspectEntity
        ident_clean = req.identifier.strip()
        suspect_stmt = select(SuspectEntity).where(
            func.lower(SuspectEntity.identifier) == ident_clean.lower(),
            SuspectEntity.platform == req.platform
        )
        suspect_res = await db.execute(suspect_stmt)
        suspect = suspect_res.scalar_one_or_none()

        if not suspect:
            suspect = SuspectEntity(
                identifier=ident_clean,
                identifier_type=req.identifier_type,
                platform=req.platform,
                risk_level=req.risk_level,
                notes=req.details,
                first_seen_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow(),
                is_active_threat=True
            )
            db.add(suspect)
            await db.flush()
        else:
            suspect.last_seen_at = datetime.utcnow()
            if req.risk_level in ("HIGH", "CRITICAL"):
                suspect.risk_level = req.risk_level
            await db.flush()

        # 3. Create IncidentSuspectLink if not already present
        link_stmt = select(IncidentSuspectLink).where(
            IncidentSuspectLink.incident_id == req.incident_id,
            IncidentSuspectLink.suspect_id == suspect.id
        )
        link_res = await db.execute(link_stmt)
        link = link_res.scalar_one_or_none()

        if not link:
            link = IncidentSuspectLink(
                incident_id=req.incident_id,
                suspect_id=suspect.id,
                modus_operandi=req.modus_operandi,
                confidence_score=req.confidence_score,
                details=req.details
            )
            db.add(link)
            await db.flush()

        await db.commit()
        await db.refresh(suspect)
        return SuspectEntityOut.model_validate(suspect)

    @staticmethod
    async def build_graph_for_case(
        db: AsyncSession,
        case_id: uuid.UUID
    ) -> GraphDataResponse:
        """
        Builds a multi-hop ego-graph for a case, discovering all connected victims,
        incidents, suspects, geographic anchors, and cross-case links.
        """
        nodes: Dict[str, GraphNode] = {}
        edges: Dict[str, GraphEdge] = {}

        # 1. Fetch Case
        case_stmt = select(Case).where(Case.id == case_id)
        case_res = await db.execute(case_stmt)
        case = case_res.scalar_one_or_none()
        if not case:
            return GraphDataResponse(nodes=[], edges=[])

        case_node_id = f"case_{case.id}"
        nodes[case_node_id] = GraphNode(
            id=case_node_id,
            label=f"Case {case.protected_case_id}",
            type="CASE",
            properties={
                "status": case.status,
                "priority": case.priority,
                "risk_score": case.risk_score or 0.0,
                "title": case.title or ""
            }
        )

        # 2. Fetch Child & Location
        child_stmt = select(Child).where(Child.id == case.child_id)
        child_res = await db.execute(child_stmt)
        child = child_res.scalar_one_or_none()
        if child:
            child_node_id = f"child_{child.id}"
            nodes[child_node_id] = GraphNode(
                id=child_node_id,
                label=f"Child {child.protected_child_id}",
                type="CHILD",
                properties={
                    "state": child.state or "",
                    "district": child.district or "",
                    "is_domestic_safety_mode": child.is_domestic_safety_mode
                }
            )
            edge_id = f"edge_{child_node_id}_{case_node_id}"
            edges[edge_id] = GraphEdge(
                id=edge_id,
                source=child_node_id,
                target=case_node_id,
                relation="INVOLVED_IN"
            )

            # Location Anchor
            if child.district:
                loc_node_id = f"loc_{child.state}_{child.district}".replace(" ", "_")
                if loc_node_id not in nodes:
                    nodes[loc_node_id] = GraphNode(
                        id=loc_node_id,
                        label=f"{child.district}, {child.state}",
                        type="LOCATION",
                        properties={"state": child.state, "district": child.district}
                    )
                loc_edge_id = f"edge_{child_node_id}_{loc_node_id}"
                edges[loc_edge_id] = GraphEdge(
                    id=loc_edge_id,
                    source=child_node_id,
                    target=loc_node_id,
                    relation="LOCATED_IN"
                )

        # 3. Fetch Incidents for this Case
        inc_stmt = select(Incident).where(Incident.case_id == case.id)
        inc_res = await db.execute(inc_stmt)
        incidents = inc_res.scalars().all()

        suspect_ids: Set[uuid.UUID] = set()

        for inc in incidents:
            inc_node_id = f"inc_{inc.id}"
            nodes[inc_node_id] = GraphNode(
                id=inc_node_id,
                label=f"{inc.incident_type.replace('_', ' ').title()}",
                type="INCIDENT",
                properties={
                    "severity": inc.severity,
                    "trust_level": inc.trust_level,
                    "description": inc.description or ""
                }
            )
            inc_edge_id = f"edge_{inc_node_id}_{case_node_id}"
            edges[inc_edge_id] = GraphEdge(
                id=inc_edge_id,
                source=inc_node_id,
                target=case_node_id,
                relation="ATTACHED_TO"
            )

            # Fetch Suspect Links
            links_stmt = select(IncidentSuspectLink).where(IncidentSuspectLink.incident_id == inc.id)
            links_res = await db.execute(links_stmt)
            links = links_res.scalars().all()

            for lk in links:
                suspect_ids.add(lk.suspect_id)
                sus_stmt = select(SuspectEntity).where(SuspectEntity.id == lk.suspect_id)
                sus_res = await db.execute(sus_stmt)
                sus = sus_res.scalar_one_or_none()
                if sus:
                    sus_node_id = f"sus_{sus.id}"
                    if sus_node_id not in nodes:
                        nodes[sus_node_id] = GraphNode(
                            id=sus_node_id,
                            label=f"{sus.identifier} ({sus.platform})",
                            type="SUSPECT",
                            properties={
                                "platform": sus.platform,
                                "risk_level": sus.risk_level,
                                "identifier_type": sus.identifier_type
                            }
                        )
                    sus_edge_id = f"edge_{sus_node_id}_{inc_node_id}"
                    edges[sus_edge_id] = GraphEdge(
                        id=sus_edge_id,
                        source=sus_node_id,
                        target=inc_node_id,
                        relation="TARGETED",
                        properties={"modus_operandi": lk.modus_operandi}
                    )

        # 4. Cross-Case "Connect the Dots": If any suspect is linked to other cases, link them in!
        for s_id in suspect_ids:
            cross_links_stmt = select(IncidentSuspectLink).where(
                IncidentSuspectLink.suspect_id == s_id
            )
            cross_res = await db.execute(cross_links_stmt)
            other_links = cross_res.scalars().all()

            for olk in other_links:
                if olk.incident_id not in [inc.id for inc in incidents]:
                    other_inc_stmt = select(Incident).where(Incident.id == olk.incident_id)
                    other_inc = (await db.execute(other_inc_stmt)).scalar_one_or_none()
                    if other_inc and other_inc.case_id != case.id:
                        other_case_stmt = select(Case).where(Case.id == other_inc.case_id)
                        other_case = (await db.execute(other_case_stmt)).scalar_one_or_none()
                        if other_case:
                            other_c_node_id = f"case_{other_case.id}"
                            if other_c_node_id not in nodes:
                                nodes[other_c_node_id] = GraphNode(
                                    id=other_c_node_id,
                                    label=f"Linked Case {other_case.protected_case_id}",
                                    type="CASE",
                                    properties={
                                        "status": other_case.status,
                                        "priority": other_case.priority,
                                        "risk_score": other_case.risk_score or 0.0,
                                        "title": other_case.title or ""
                                    }
                                )
                            cross_edge_id = f"cross_edge_sus_{s_id}_{other_c_node_id}"
                            edges[cross_edge_id] = GraphEdge(
                                id=cross_edge_id,
                                source=f"sus_{s_id}",
                                target=other_c_node_id,
                                relation="SERIAL_OFFENDER_LINK",
                                properties={"shared_modus_operandi": olk.modus_operandi}
                            )

        return GraphDataResponse(
            nodes=list(nodes.values()),
            edges=list(edges.values())
        )

    @staticmethod
    async def connect_the_dots(
        db: AsyncSession,
        identifier: str
    ) -> ConnectTheDotsResponse:
        """
        Traces every victim child, case, and jurisdiction touching a suspect handle or phone.
        """
        ident_clean = identifier.strip()
        suspect_stmt = select(SuspectEntity).where(
            func.lower(SuspectEntity.identifier) == ident_clean.lower()
        )
        suspect_res = await db.execute(suspect_stmt)
        suspects = suspect_res.scalars().all()

        if not suspects:
            return ConnectTheDotsResponse(
                suspect_identifier=identifier,
                platform="UNKNOWN",
                risk_level="LOW",
                victim_children=[],
                associated_cases=[],
                modus_operandi=[],
                districts_involved=[],
                cross_jurisdictional=False
            )

        sus = suspects[0]
        sus_ids = [s.id for s in suspects]

        links_stmt = select(IncidentSuspectLink).where(IncidentSuspectLink.suspect_id.in_(sus_ids))
        links = (await db.execute(links_stmt)).scalars().all()

        victim_children_dict: Dict[uuid.UUID, Dict[str, Any]] = {}
        associated_cases_dict: Dict[uuid.UUID, Dict[str, Any]] = {}
        mo_set: Set[str] = set()
        districts_set: Set[str] = set()

        for lk in links:
            mo_set.add(lk.modus_operandi)
            inc_stmt = select(Incident).where(Incident.id == lk.incident_id)
            inc = (await db.execute(inc_stmt)).scalar_one_or_none()
            if inc:
                case_stmt = select(Case).where(Case.id == inc.case_id)
                c = (await db.execute(case_stmt)).scalar_one_or_none()
                if c:
                    associated_cases_dict[c.id] = {
                        "case_id": str(c.id),
                        "protected_case_id": c.protected_case_id,
                        "status": c.status,
                        "priority": c.priority,
                        "risk_score": c.risk_score or 0.0
                    }
                    child_stmt = select(Child).where(Child.id == c.child_id)
                    ch = (await db.execute(child_stmt)).scalar_one_or_none()
                    if ch:
                        victim_children_dict[ch.id] = {
                            "child_id": str(ch.id),
                            "protected_child_id": ch.protected_child_id,
                            "state": ch.state or "Unknown",
                            "district": ch.district or "Unknown"
                        }
                        if ch.district:
                            districts_set.add(ch.district)

        return ConnectTheDotsResponse(
            suspect_identifier=sus.identifier,
            platform=sus.platform,
            risk_level=sus.risk_level,
            victim_children=list(victim_children_dict.values()),
            associated_cases=list(associated_cases_dict.values()),
            modus_operandi=list(mo_set),
            districts_involved=list(districts_set),
            cross_jurisdictional=len(districts_set) > 1
        )

    @staticmethod
    async def find_predatory_clusters(
        db: AsyncSession
    ) -> PredatoryClustersResponse:
        """
        Discovers serial predators and coordinated predatory rings targeting multiple victims.
        """
        stmt = select(SuspectEntity)
        suspects = (await db.execute(stmt)).scalars().all()

        clusters: List[SuspectCluster] = []
        multi_victim_count = 0

        for sus in suspects:
            links_stmt = select(IncidentSuspectLink).where(IncidentSuspectLink.suspect_id == sus.id)
            links = (await db.execute(links_stmt)).scalars().all()

            victim_ids: Set[str] = set()
            case_ids: Set[str] = set()
            mo_list: Set[str] = set()
            geo_list: Set[str] = set()

            for lk in links:
                mo_list.add(lk.modus_operandi)
                inc_stmt = select(Incident).where(Incident.id == lk.incident_id)
                inc = (await db.execute(inc_stmt)).scalar_one_or_none()
                if inc:
                    case_stmt = select(Case).where(Case.id == inc.case_id)
                    c = (await db.execute(case_stmt)).scalar_one_or_none()
                    if c:
                        case_ids.add(c.protected_case_id)
                        child_stmt = select(Child).where(Child.id == c.child_id)
                        ch = (await db.execute(child_stmt)).scalar_one_or_none()
                        if ch:
                            victim_ids.add(ch.protected_child_id)
                            if ch.district:
                                geo_list.add(f"{ch.district}, {ch.state}")

            if len(victim_ids) >= 1:
                if len(victim_ids) >= 2:
                    multi_victim_count += 1
                clusters.append(SuspectCluster(
                    cluster_id=f"cluster_{sus.id}",
                    suspect_identifier=sus.identifier,
                    identifier_type=sus.identifier_type,
                    platform=sus.platform,
                    risk_level=sus.risk_level,
                    linked_cases_count=len(case_ids),
                    victim_child_ids=list(victim_ids),
                    modus_operandi_list=list(mo_list),
                    geographic_reach=list(geo_list),
                    first_seen_at=sus.first_seen_at,
                    last_seen_at=sus.last_seen_at
                ))

        clusters.sort(key=lambda x: (len(x.victim_child_ids), x.linked_cases_count), reverse=True)
        return PredatoryClustersResponse(
            clusters=clusters,
            total_clusters=len(clusters),
            multi_victim_predators_count=multi_victim_count
        )

    @staticmethod
    async def get_graph_statistics(db: AsyncSession) -> GraphStatsResponse:
        """
        Calculates platform-wide network metrics across cases, victims, and offenders.
        """
        suspects_count = (await db.execute(select(func.count(SuspectEntity.id)))).scalar() or 0
        cases_count = (await db.execute(select(func.count(Case.id)))).scalar() or 0
        incidents_count = (await db.execute(select(func.count(Incident.id)))).scalar() or 0
        links_count = (await db.execute(select(func.count(IncidentSuspectLink.id)))).scalar() or 0

        clusters = await KnowledgeGraphService.find_predatory_clusters(db)

        # Estimate nodes = suspects + cases + incidents + distinct children
        children_count = (await db.execute(select(func.count(Child.id)))).scalar() or 0
        total_nodes = suspects_count + cases_count + incidents_count + children_count
        total_edges = incidents_count + links_count + cases_count

        return GraphStatsResponse(
            total_nodes=total_nodes,
            total_edges=total_edges,
            suspects_count=suspects_count,
            cases_count=cases_count,
            incidents_count=incidents_count,
            multi_victim_predators_count=clusters.multi_victim_predators_count
        )
