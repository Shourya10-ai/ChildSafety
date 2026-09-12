import asyncio
import uuid
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath("backend"))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.db.base import Base
from app.models.user import User
from app.models.child import Child
from app.models.case import Case, Incident
from app.models.knowledge_graph import SuspectEntity, IncidentSuspectLink

from app.services.knowledge_graph_service import KnowledgeGraphService
from app.services.case_similarity_service import CaseSimilarityService
from app.services.risk_engine_service import RiskEngineService
from app.schemas.knowledge_graph import LinkSuspectRequest

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

async def setup_test_db():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, Session

async def run_all_tests():
    engine, Session = await setup_test_db()
    async with Session() as db:
        print("\n=======================================================")
        print("PHASE 10: KNOWLEDGE GRAPH, SIMILARITY & RISK ENGINE TESTS")
        print("=======================================================\n")

        # --- SEEDING BASE DATA ---
        u1 = User(email="child1@test.com", hashed_password="hash", full_name="Aarav Sharma", role="child")
        u2 = User(email="child2@test.com", hashed_password="hash", full_name="Ananya Naik", role="child")
        db.add_all([u1, u2])
        await db.flush()

        ch1 = Child(user_id=u1.id, protected_child_id="C-DL-SDL-1001", display_name="Aarav", state="Delhi", district="South Delhi", is_domestic_safety_mode=False)
        ch2 = Child(user_id=u2.id, protected_child_id="C-GA-NGO-2002", display_name="Ananya", state="Goa", district="North Goa", is_domestic_safety_mode=True)
        db.add_all([ch1, ch2])
        await db.flush()

        c1 = Case(child_id=ch1.id, protected_case_id="CS-2026-1001", status="INVESTIGATING", priority="critical", title="Online Grooming & Sextortion")
        c2 = Case(child_id=ch2.id, protected_case_id="CS-2026-2002", status="PENDING_TRIAGE", priority="high", title="Social Media Coercion")
        c3 = Case(child_id=ch1.id, protected_case_id="CS-2026-3003", status="RESOLVED", priority="low", title="Lost Property Report")
        db.add_all([c1, c2, c3])
        await db.flush()

        inc1 = Incident(case_id=c1.id, incident_type="grooming", severity="critical", description="Offender lured child with gaming skins then demanded private photos", trust_level="moderator_verified")
        inc2 = Incident(case_id=c1.id, incident_type="sextortion", severity="critical", description="Offender threatened to distribute private photos on Instagram", trust_level="moderator_verified")
        inc3 = Incident(case_id=c2.id, incident_type="grooming", severity="high", description="Offender sent threatening messages demanding meetup in Goa", trust_level="unverified")
        inc4 = Incident(case_id=c3.id, incident_type="other", severity="low", description="Child misplaced school identity card", trust_level="unverified")
        db.add_all([inc1, inc2, inc3, inc4])
        await db.commit()

        # -------------------------------------------------------------
        # TEST 1: Link Suspects & Build Ego-Graph
        # -------------------------------------------------------------
        print("--- Test 1: Linking Suspect Entity & Building Case Ego-Graph ---")
        sus_out = await KnowledgeGraphService.link_suspect_to_incident(
            db,
            LinkSuspectRequest(
                incident_id=inc1.id,
                identifier="@predator_shadow",
                identifier_type="SOCIAL_HANDLE",
                platform="INSTAGRAM",
                modus_operandi="GROOMING_GIFTING",
                details="Targeted victim on Instagram DM",
                risk_level="CRITICAL"
            )
        )
        assert sus_out.identifier == "@predator_shadow"
        assert sus_out.platform == "INSTAGRAM"
        print("  -> Linked suspect @predator_shadow to Incident 1: SUCCESS")

        # Also link sextortion incident
        await KnowledgeGraphService.link_suspect_to_incident(
            db,
            LinkSuspectRequest(
                incident_id=inc2.id,
                identifier="@predator_shadow",
                identifier_type="SOCIAL_HANDLE",
                platform="INSTAGRAM",
                modus_operandi="SEXTORTION",
                details="Coerced child via Instagram",
                risk_level="CRITICAL"
            )
        )

        graph = await KnowledgeGraphService.build_graph_for_case(db, c1.id)
        node_types = {n.type for n in graph.nodes}
        edge_rels = {e.relation for e in graph.edges}
        assert "CASE" in node_types
        assert "CHILD" in node_types
        assert "INCIDENT" in node_types
        assert "SUSPECT" in node_types
        assert "LOCATION" in node_types
        assert "INVOLVED_IN" in edge_rels
        assert "TARGETED" in edge_rels
        print(f"  -> Ego-Graph generated with {len(graph.nodes)} nodes and {len(graph.edges)} edges: PASS")

        # -------------------------------------------------------------
        # TEST 2: Cross-Case "Connect the Dots" & Predatory Clusters
        # -------------------------------------------------------------
        print("\n--- Test 2: Cross-Case 'Connect the Dots' & Predatory Clusters ---")
        # Link the SAME predator to Child 2 in Goa!
        await KnowledgeGraphService.link_suspect_to_incident(
            db,
            LinkSuspectRequest(
                incident_id=inc3.id,
                identifier="@predator_shadow",
                identifier_type="SOCIAL_HANDLE",
                platform="INSTAGRAM",
                modus_operandi="MEETUP_ENTICEMENT",
                details="Tried to arrange physical meetup in Goa",
                risk_level="CRITICAL"
            )
        )

        dots = await KnowledgeGraphService.connect_the_dots(db, "@predator_shadow")
        assert len(dots.victim_children) == 2, f"Expected 2 victim children, got {len(dots.victim_children)}"
        assert len(dots.associated_cases) == 2, f"Expected 2 associated cases, got {len(dots.associated_cases)}"
        assert dots.cross_jurisdictional is True, "Expected cross_jurisdictional == True across Delhi and Goa"
        assert "South Delhi" in dots.districts_involved
        assert "North Goa" in dots.districts_involved
        print(f"  -> Connected the dots: Suspect @predator_shadow linked to {len(dots.victim_children)} victims across {len(dots.districts_involved)} jurisdictions (Delhi & Goa): PASS")

        clusters = await KnowledgeGraphService.find_predatory_clusters(db)
        assert clusters.multi_victim_predators_count >= 1
        assert clusters.clusters[0].suspect_identifier == "@predator_shadow"
        print(f"  -> Detected multi-victim predatory cluster with {clusters.clusters[0].linked_cases_count} cases: PASS")

        # -------------------------------------------------------------
        # TEST 3: Multi-Dimensional Case Similarity Engine
        # -------------------------------------------------------------
        print("\n--- Test 3: Multi-Dimensional Case Similarity Engine ---")
        sim_response = await CaseSimilarityService.find_similar_cases(db, c1.id, top_k=3)
        assert len(sim_response.top_matches) >= 1
        top_match = sim_response.top_matches[0]
        assert top_match.case_id == c2.id, f"Expected top match to be Case 2 (CS-2026-2002), got {top_match.protected_case_id}"
        assert "@predator_shadow" in [s.lower() for s in top_match.shared_suspects]
        assert top_match.similarity_score >= 0.35
        print(f"  -> Top match for Case 1 is Case 2 (Score: {top_match.similarity_score}): PASS")
        print(f"     Match Reasons: {top_match.match_reasons}")

        # -------------------------------------------------------------
        # TEST 4: Predictive Multi-Factor Risk Engine & Statutory Citations
        # -------------------------------------------------------------
        print("\n--- Test 4: Predictive Multi-Factor Risk Engine & Statutory Citations ---")
        risk_c1 = await RiskEngineService.evaluate_case_risk(db, c1.id)
        assert risk_c1.composite_risk_score >= 0.70, f"Expected critical/high risk >= 0.70, got {risk_c1.composite_risk_score}"
        assert risk_c1.threat_tier in ("HIGH", "CRITICAL")
        
        statutory_acts = [c.act for c in risk_c1.statutory_citations]
        assert any("POCSO Act" in act for act in statutory_acts), "Expected POCSO Act statutory citation"
        print(f"  -> Case 1 Evaluated: Risk Score {risk_c1.composite_risk_score} [{risk_c1.threat_tier}]")
        print(f"     Statutory Citations: {[c.section + ' ' + c.act for c in risk_c1.statutory_citations]}")
        print(f"     Recommended Interventions: {risk_c1.recommended_interventions[:2]}")

        # Evaluate Domestic Safety Child 2
        risk_ch2 = await RiskEngineService.evaluate_child_risk(db, ch2.id)
        assert risk_ch2.factors.vulnerability_score >= 0.80, "Domestic safety child must have elevated vulnerability"
        print(f"  -> Child 2 (Domestic Safety Mode) Evaluated: Vulnerability Score {risk_ch2.factors.vulnerability_score}: PASS")

        # -------------------------------------------------------------
        # TEST 5: Graph Statistics
        # -------------------------------------------------------------
        print("\n--- Test 5: Graph Statistics ---")
        stats = await KnowledgeGraphService.get_graph_statistics(db)
        assert stats.suspects_count >= 1
        assert stats.cases_count >= 3
        assert stats.multi_victim_predators_count >= 1
        print(f"  -> Graph Stats: Nodes={stats.total_nodes}, Edges={stats.total_edges}, Suspects={stats.suspects_count}, Multi-Victim Predators={stats.multi_victim_predators_count}: PASS")

        print("\n=======================================================")
        print("ALL PHASE 10 BACKEND TESTS PASSED WITH 100% SUCCESS! [PASS]")
        print("=======================================================\n")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_all_tests())
