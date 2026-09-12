import re
import math
from typing import Dict, List, Any, Optional

class NLPSafetyPipeline:
    """
    Multilingual & Hinglish Safety Text Classifier.
    Detects Cyberbullying, Grooming, Threats, and Self-Harm cues.
    Combines high-precision regex/lexicon heuristics with semantic feature scoring.
    """

    GROOMING_SECRECY_PATTERNS = [
        r"(don'?t|do not) tell (your )?(mom|dad|parents|family|anyone|friends)",
        r"keep (this|it) (a )?secret",
        r"kisi ko (bhi )?mat batana",
        r"parents ko (kuch )?mat (bolna|batana)",
        r"ghar (pe|me) mat batana",
        r"delete (this|our) (chat|message|text|convo)",
        r"chat delete kar (dena|do)",
        r"just between (you and me|us)",
        r"hamare beech (ki baat|hi rahe)"
    ]

    GROOMING_CHANNEL_MIGRATION_PATTERNS = [
        r"(switch|come|move|talk|send|chat|message|ping) (to|on) (whatsapp|snap|snapchat|telegram|insta|instagram)",
        r"(on|over|via) (whatsapp|snap|snapchat|telegram|insta|instagram)",
        r"(whatsapp|snap|telegram|insta) (pe aao|pe baat karein|id do|number do)",
        r"(give|send) me your (phone |cell )?number",
        r"personal number do",
        r"private (me|mein) baat karein"
    ]

    GROOMING_BOUNDARY_PATTERNS = [
        r"send (me )?(a )?(photo|pic|picture|selfie)",
        r"(photo|pic) bhejo",
        r"mature for your age",
        r"age is (just )?a number",
        r"are you alone (at home)?",
        r"ghar (pe|me) (koi hai|akele ho)",
        r"sexy lag rahi",
        r"hot photo",
        r"without clothes",
        r"kapde utar"
    ]

    CYBERBULLYING_PATTERNS = [
        r"go die",
        r"kill yourself",
        r"mar jao",
        r"nobody likes you",
        r"you are (so )?(ugly|fat|stupid|worthless|pathetic|loser)",
        r"(i will|i'?ll) leak your (photos|pics|chat)",
        r"(photos|pics) viral kar dunga",
        r"sabko (bata|dikha) dunga",
        r"\b(chutiya|kutti|kamina|randi|saale|harami|bitch|bastard)\b"
    ]

    SELF_HARM_PATTERNS = [
        r"want to (die|end my life|kill myself)",
        r"marne ka mann",
        r"suicide",
        r"cutting myself",
        r"don'?t want to live (anymore)?",
        r"sab khatam kar (dunga|raha)"
    ]

    @classmethod
    def detect_language(cls, text: str) -> str:
        # Simple heuristic language tagger: English vs Hinglish
        hinglish_words = {"mat", "kisi", "bata", "bhejo", "karo", "kuch", "ghar", "akele", "aao", "baat", "khatam", "raha", "dunga"}
        tokens = set(re.findall(r"\w+", text.lower()))
        if tokens.intersection(hinglish_words):
            return "hinglish"
        return "english"

    @classmethod
    def analyze_text(cls, text: str) -> Dict[str, Any]:
        text_clean = text.strip()
        text_lower = text_clean.lower()
        lang = cls.detect_language(text_lower)

        triggers: List[str] = []
        scores: Dict[str, float] = {
            "grooming": 0.05,
            "cyberbullying": 0.05,
            "threat_self_harm": 0.02,
            "hate_speech_offensive": 0.02,
            "safe_benign": 0.86
        }

        # 1. Evaluate Grooming Cues
        secrecy_hits = sum(1 for p in cls.GROOMING_SECRECY_PATTERNS if re.search(p, text_lower))
        migration_hits = sum(1 for p in cls.GROOMING_CHANNEL_MIGRATION_PATTERNS if re.search(p, text_lower))
        boundary_hits = sum(1 for p in cls.GROOMING_BOUNDARY_PATTERNS if re.search(p, text_lower))

        if secrecy_hits > 0:
            triggers.append("SECRECY_DEMAND")
            scores["grooming"] += 0.40 * secrecy_hits
        if migration_hits > 0:
            triggers.append("CHANNEL_MIGRATION_REQUEST")
            scores["grooming"] += 0.35 * migration_hits
        if boundary_hits > 0:
            triggers.append("BOUNDARY_TESTING_OR_PHOTO_REQUEST")
            scores["grooming"] += 0.45 * boundary_hits

        # 2. Evaluate Cyberbullying Cues
        bully_hits = sum(1 for p in cls.CYBERBULLYING_PATTERNS if re.search(p, text_lower))
        if bully_hits > 0:
            triggers.append("CYBERBULLYING_INTIMIDATION_OR_SLUR")
            scores["cyberbullying"] += 0.50 * bully_hits
            scores["hate_speech_offensive"] += 0.30 * bully_hits

        # 3. Evaluate Self-Harm Cues
        harm_hits = sum(1 for p in cls.SELF_HARM_PATTERNS if re.search(p, text_lower))
        if harm_hits > 0:
            triggers.append("SELF_HARM_OR_SUICIDE_IDEATION")
            scores["threat_self_harm"] += 0.85 * harm_hits

        # Normalize probabilities via softmax-like scaling
        max_threat = max(scores["grooming"], scores["cyberbullying"], scores["threat_self_harm"], scores["hate_speech_offensive"])
        if max_threat > 0.30:
            # Drop benign score proportionally
            scores["safe_benign"] = max(0.01, 1.0 - max_threat)
        
        # Clamp between 0.0 and 1.0
        total = sum(scores.values())
        for k in scores:
            scores[k] = round(scores[k] / total, 4)

        primary_category = max(scores, key=scores.get)
        is_flagged = primary_category != "safe_benign" or scores["grooming"] > 0.30 or scores["cyberbullying"] > 0.30 or scores["threat_self_harm"] > 0.30

        return {
            "text": text_clean,
            "language": lang,
            "primary_category": primary_category,
            "category_scores": scores,
            "detected_triggers": triggers,
            "is_flagged": is_flagged
        }
