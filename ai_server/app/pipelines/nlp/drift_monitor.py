from __future__ import annotations
import math
import re
import time
from collections import Counter, deque
from typing import Any, Dict, List, Optional, Set

class ConceptDriftMonitor:
    """
    Concept Drift & Active Learning Monitor for Child Safety AI Models.
    Tracks out-of-vocabulary (OOV) slang frequency, vernacular shifts,
    category distribution divergence, and queues uncertain edge-cases.
    """

    BASE_VOCABULARY: Set[str] = {
        # Core English
        "hello", "hi", "hey", "how", "are", "you", "doing", "what", "where", "why",
        "who", "when", "can", "could", "would", "should", "will", "is", "was", "am",
        "have", "has", "had", "do", "does", "did", "school", "homework", "friend", "friends",
        "play", "game", "gaming", "online", "chat", "talk", "photo", "pic", "picture",
        "secret", "parents", "mom", "dad", "family", "house", "home", "alone",
        "die", "kill", "suicide", "ugly", "loser", "stupid", "delete", "whatsapp",
        "instagram", "snapchat", "telegram", "number", "phone", "call", "send",
        # Core Hinglish / Indian vernacular
        "mat", "kisi", "bata", "batana", "bolna", "bhejo", "karo", "kuch", "ghar",
        "akele", "aao", "baat", "khatam", "raha", "dunga", "kar", "dena", "hamare",
        "beech", "rahe", "pe", "me", "mein", "sexy", "kapde", "mar", "jao", "marne",
        "mann", "sabko", "dikha", "viral", "chutiya", "kutti", "kamina", "randi",
        "saale", "harami", "bhai", "yaar", "dost", "kaise", "kya", "kyun", "kahan"
    }

    BASELINE_CATEGORY_DIST: Dict[str, float] = {
        "safe_benign": 0.85,
        "grooming": 0.05,
        "cyberbullying": 0.05,
        "threat_self_harm": 0.03,
        "hate_speech_offensive": 0.02
    }

    def __init__(self, window_size: int = 500, oov_threshold: float = 0.20):
        self.window_size = window_size
        self.oov_threshold = oov_threshold
        self.vocabulary: Set[str] = set(self.BASE_VOCABULARY)
        
        self.total_samples: int = 0
        self.recent_tokens: deque = deque(maxlen=window_size * 10)
        self.recent_oov_count: int = 0
        self.recent_total_tokens: int = 0
        
        self.recent_predictions: deque = deque(maxlen=window_size)
        self.active_learning_queue: deque = deque(maxlen=200)

    def record_inference(
        self,
        text: str,
        nlp_analysis: Dict[str, Any],
        risk_evaluation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Record and inspect inference output for drift cues.
        """
        self.total_samples += 1
        tokens = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
        
        oov_tokens_in_sample = [t for t in tokens if t not in self.vocabulary]
        sample_oov_ratio = len(oov_tokens_in_sample) / max(1, len(tokens))

        for t in tokens:
            self.recent_tokens.append(t)
        self.recent_oov_count += len(oov_tokens_in_sample)
        self.recent_total_tokens += len(tokens)

        # Cap sliding token counts
        if self.recent_total_tokens > self.window_size * 20:
            self.recent_total_tokens = self.window_size * 10
            self.recent_oov_count = int(self.recent_oov_count * 0.5)

        primary_cat = nlp_analysis.get("primary_category", "safe_benign")
        composite_risk = risk_evaluation.get("composite_risk_score", 0.0)
        risk_level = risk_evaluation.get("risk_level", "LOW")

        self.recent_predictions.append({
            "timestamp": time.time(),
            "primary_category": primary_cat,
            "risk_score": composite_risk,
            "risk_level": risk_level,
            "oov_ratio": sample_oov_ratio
        })

        # Active Learning Candidate Heuristic:
        # 1. High ambiguity boundary zone (0.30 <= composite_risk <= 0.70)
        # 2. Or high slang/OOV ratio with medium risk
        is_active_learning_candidate = False
        reasons = []

        if 0.30 <= composite_risk <= 0.70:
            is_active_learning_candidate = True
            reasons.append("DECISION_BOUNDARY_UNCERTAINTY")
        
        if sample_oov_ratio > 0.35 and len(tokens) >= 3:
            is_active_learning_candidate = True
            reasons.append("HIGH_OOV_SLANG_DENSITY")

        if is_active_learning_candidate:
            candidate_entry = {
                "sample_id": f"drift-al-{self.total_samples}",
                "text": text,
                "oov_tokens": oov_tokens_in_sample,
                "primary_category": primary_cat,
                "composite_risk": composite_risk,
                "risk_level": risk_level,
                "flagged_reasons": reasons,
                "timestamp": time.time()
            }
            self.active_learning_queue.append(candidate_entry)

        return {
            "oov_ratio": round(sample_oov_ratio, 3),
            "oov_tokens": oov_tokens_in_sample,
            "is_active_learning_candidate": is_active_learning_candidate
        }

    def compute_metrics(self) -> Dict[str, Any]:
        """
        Calculate population stability index (PSI) / divergence and slang drift metrics.
        """
        current_oov_rate = (
            self.recent_oov_count / max(1, self.recent_total_tokens)
            if self.recent_total_tokens > 0 else 0.0
        )

        # Calculate current category frequencies
        pred_count = len(self.recent_predictions)
        current_dist: Dict[str, float] = {}
        if pred_count > 0:
            counts = Counter(p["primary_category"] for p in self.recent_predictions)
            for cat in self.BASELINE_CATEGORY_DIST:
                current_dist[cat] = counts.get(cat, 0) / pred_count
        else:
            current_dist = dict(self.BASELINE_CATEGORY_DIST)

        # Calculate simple Kullback-Leibler / Jensen-Shannon approximation for distribution shift
        drift_distance = 0.0
        for cat, base_prob in self.BASELINE_CATEGORY_DIST.items():
            curr_prob = current_dist.get(cat, 0.001)
            curr_prob = max(0.001, curr_prob)
            drift_distance += abs(curr_prob - base_prob)

        drift_detected = (
            current_oov_rate > self.oov_threshold or
            drift_distance > 0.40
        )

        return {
            "total_inferences": self.total_samples,
            "window_size": self.window_size,
            "current_window_predictions": pred_count,
            "current_oov_rate": round(current_oov_rate, 4),
            "oov_threshold": self.oov_threshold,
            "category_distribution": {k: round(v, 4) for k, v in current_dist.items()},
            "baseline_distribution": self.BASELINE_CATEGORY_DIST,
            "distribution_drift_score": round(drift_distance, 4),
            "drift_detected": drift_detected,
            "active_learning_queue_depth": len(self.active_learning_queue)
        }

    def get_active_learning_samples(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieve highest priority samples queued for human annotation.
        """
        samples = list(self.active_learning_queue)
        samples.sort(key=lambda x: abs(0.50 - x.get("composite_risk", 0.0)))
        return samples[:limit]

    def register_new_slang_words(self, words: List[str]) -> int:
        """
        Incorporate newly approved vernacular slang into known vocabulary.
        """
        added = 0
        for w in words:
            w_clean = w.strip().lower()
            if w_clean and w_clean not in self.vocabulary:
                self.vocabulary.add(w_clean)
                added += 1
        return added

# Singleton instance
drift_monitor = ConceptDriftMonitor()
