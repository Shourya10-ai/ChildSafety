from __future__ import annotations
import unittest
from app.pipelines.nlp.nlp_safety_pipeline import NLPSafetyPipeline
from app.risk_engine.risk_scorer import RiskScoringEngine
from app.pipelines.nlp.drift_monitor import ConceptDriftMonitor
from app.rag.schemas import ModeratorGuidanceQuery
from app.rag.statutory_rag import StatutoryRAGCopilot

class TestSafetyNLPPipeline(unittest.TestCase):

    def test_benign_text_english(self):
        text = "Hey are we playing Minecraft today after finishing our science homework?"
        res = NLPSafetyPipeline.analyze_text(text)
        self.assertFalse(res["is_flagged"])
        self.assertEqual(res["primary_category"], "safe_benign")
        
        risk = RiskScoringEngine.calculate_risk(res)
        self.assertEqual(risk["risk_level"], "LOW")
        self.assertLess(risk["composite_risk_score"], 0.30)
        self.assertFalse(risk["requires_human_moderator_review"])

    def test_grooming_hinglish_secrecy_and_photo(self):
        text = "kisi ko mat batana, send me photo without clothes on whatsapp"
        res = NLPSafetyPipeline.analyze_text(text)
        self.assertTrue(res["is_flagged"])
        self.assertIn("SECRECY_DEMAND", res["detected_triggers"])
        self.assertIn("BOUNDARY_TESTING_OR_PHOTO_REQUEST", res["detected_triggers"])
        self.assertIn("CHANNEL_MIGRATION_REQUEST", res["detected_triggers"])
        self.assertEqual(res["language"], "hinglish")

        risk = RiskScoringEngine.calculate_risk(res)
        self.assertIn(risk["risk_level"], ["HIGH", "CRITICAL"])
        self.assertIn("POCSO_ACT_SEC_11_12", risk["statutory_tags"])
        self.assertTrue(risk["requires_human_moderator_review"])
        self.assertTrue(risk["requires_immediate_sla_escalation"])

    def test_cyberbullying_and_threat(self):
        text = "You are so ugly and worthless. I will leak your photos online and viral kar dunga"
        res = NLPSafetyPipeline.analyze_text(text)
        self.assertTrue(res["is_flagged"])
        self.assertIn("CYBERBULLYING_INTIMIDATION_OR_SLUR", res["detected_triggers"])
        self.assertGreater(res["category_scores"]["cyberbullying"], 0.3)

        risk = RiskScoringEngine.calculate_risk(res)
        self.assertIn(risk["risk_level"], ["MEDIUM", "HIGH", "CRITICAL"])
        self.assertIn("BNS_2023_SEC_78_79_351", risk["statutory_tags"])

    def test_self_harm_detection(self):
        text = "I don't want to live anymore, want to end my life"
        res = NLPSafetyPipeline.analyze_text(text)
        self.assertTrue(res["is_flagged"])
        self.assertIn("SELF_HARM_OR_SUICIDE_IDEATION", res["detected_triggers"])

        risk = RiskScoringEngine.calculate_risk(res)
        self.assertEqual(risk["risk_level"], "CRITICAL")
        self.assertIn("CWC_IMMEDIATE_CARE_PROTECTION", risk["statutory_tags"])
        self.assertTrue(risk["requires_immediate_sla_escalation"])

    def test_drift_monitor_oov_and_active_learning(self):
        monitor = ConceptDriftMonitor(window_size=10, oov_threshold=0.15)
        text = "wassup skibidi rizzler gyatt no cap frfr"
        res = NLPSafetyPipeline.analyze_text(text)
        risk = RiskScoringEngine.calculate_risk(res)
        drift = monitor.record_inference(text, res, risk)

        self.assertGreater(drift["oov_ratio"], 0.3)
        metrics = monitor.compute_metrics()
        self.assertEqual(metrics["total_inferences"], 1)
        self.assertGreater(metrics["current_oov_rate"], 0.0)

    def test_statutory_rag_pocso_guidance(self):
        query = ModeratorGuidanceQuery(
            incident_type="online_grooming",
            observed_behavior="Suspect demanded child keep chats secret and requested photos",
            victim_age=13,
            suspect_relationship="Online gaming acquaintance",
            query_text="What are mandatory reporting timelines for cyber grooming under Indian law?"
        )
        guidance = StatutoryRAGCopilot.generate_grounded_guidance(query)
        self.assertTrue(guidance.statutory_grounded)
        self.assertTrue(guidance.mandatory_reporting_required)
        self.assertGreater(len(guidance.statutory_citations), 0)
        self.assertTrue(any("POCSO" in c.statute_name for c in guidance.statutory_citations))

if __name__ == "__main__":
    unittest.main()
