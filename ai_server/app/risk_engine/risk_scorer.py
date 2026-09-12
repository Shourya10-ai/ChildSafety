from typing import Dict, List, Any

class RiskScoringEngine:
    """
    Risk Assessment Engine for Child Safety Incidents.
    Computes a composite risk score based on category severity, behavioral intent, and secrecy indicators.
    """

    CATEGORY_WEIGHTS = {
        "threat_self_harm": 1.0,
        "grooming": 0.90,
        "cyberbullying": 0.75,
        "hate_speech_offensive": 0.50,
        "safe_benign": 0.0
    }

    TRIGGER_MULTIPLIERS = {
        "SECRECY_DEMAND": 0.25,
        "BOUNDARY_TESTING_OR_PHOTO_REQUEST": 0.35,
        "CHANNEL_MIGRATION_REQUEST": 0.20,
        "CYBERBULLYING_INTIMIDATION_OR_SLUR": 0.30,
        "SELF_HARM_OR_SUICIDE_IDEATION": 0.50
    }

    @classmethod
    def calculate_risk(cls, analysis: Dict[str, Any]) -> Dict[str, Any]:
        primary_cat = analysis.get("primary_category", "safe_benign")
        cat_scores = analysis.get("category_scores", {})
        triggers = analysis.get("detected_triggers", [])

        # Base risk from weighted probabilities
        base_risk = 0.0
        for cat, weight in cls.CATEGORY_WEIGHTS.items():
            base_risk += cat_scores.get(cat, 0.0) * weight

        # Add trigger penalties
        trigger_bonus = sum(cls.TRIGGER_MULTIPLIERS.get(t, 0.1) for t in triggers)
        composite_score = min(1.0, round(base_risk + trigger_bonus, 3))

        # Determine Discrete Risk Level
        if composite_score >= 0.85 or "SELF_HARM_OR_SUICIDE_IDEATION" in triggers:
            risk_level = "CRITICAL"
        elif composite_score >= 0.65 or ("SECRECY_DEMAND" in triggers and "BOUNDARY_TESTING_OR_PHOTO_REQUEST" in triggers):
            risk_level = "HIGH"
        elif composite_score >= 0.35:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Map to Indian statutory action tags
        statutory_tags = []
        if "BOUNDARY_TESTING_OR_PHOTO_REQUEST" in triggers or cat_scores.get("grooming", 0) > 0.4:
            statutory_tags.append("POCSO_ACT_SEC_11_12")
        if "CYBERBULLYING_INTIMIDATION_OR_SLUR" in triggers or cat_scores.get("cyberbullying", 0) > 0.4:
            statutory_tags.append("BNS_2023_SEC_78_79_351")
        if "SELF_HARM_OR_SUICIDE_IDEATION" in triggers:
            statutory_tags.append("CWC_IMMEDIATE_CARE_PROTECTION")

        return {
            "composite_risk_score": composite_score,
            "risk_level": risk_level,
            "confidence_score": round(max(cat_scores.values()) if cat_scores else 0.85, 3),
            "statutory_tags": statutory_tags,
            "requires_human_moderator_review": risk_level in ["CRITICAL", "HIGH", "MEDIUM"],
            "requires_immediate_sla_escalation": risk_level == "CRITICAL"
        }
