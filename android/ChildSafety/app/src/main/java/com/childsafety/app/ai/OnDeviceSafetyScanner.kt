package com.childsafety.app.ai

import android.content.Context
import timber.log.Timber

enum class ThreatLevel {
    SAFE,
    SUSPICIOUS,
    HIGH_RISK,
    CRITICAL
}

enum class SafetyAction {
    NONE,
    ADVICE_CHIP,
    SHOW_DECOY_EXIT,
    EMERGENCY_INTERCEPT
}

data class SafetyScanResult(
    val threatLevel: ThreatLevel,
    val matchedCategories: List<String>,
    val riskScore: Float,
    val recommendedAction: SafetyAction,
    val guidanceText: String
)

/**
 * On-Device Content Safety & Edge Heuristic Scanner.
 * Operates 100% offline on the child's device before network transmission,
 * ensuring zero latency for distress interception, blackmail detection, and decoy exits.
 */
class OnDeviceSafetyScanner(private val context: Context) {

    private val extortionKeywords = listOf(
        "leak", "post your", "send photo", "send pic", "nude", "private picture",
        "show me", "or i will share", "blackmail", "pay me", "tell everyone"
    )

    private val secrecyKeywords = listOf(
        "don't tell", "secret", "dont tell your parents", "delete chat",
        "keep this between us", "hide this", "our little secret", "promise not to say"
    )

    private val groomingKeywords = listOf(
        "meet me", "come alone", "where do you live", "what school",
        "give me your number", "send location", "are you home alone", "hotel", "park alone"
    )

    private val selfHarmKeywords = listOf(
        "kill myself", "want to die", "suicide", "end my life", "hurt myself", "cutting myself"
    )

    /**
     * Scans outbound or inbound text on-device.
     */
    fun scanText(text: String): SafetyScanResult {
        val lower = text.lowercase()
        val matchedCategories = mutableListOf<String>()
        var score = 0.0f

        // 1. Self Harm / Extreme Emergency Check
        val hasSelfHarm = selfHarmKeywords.any { lower.contains(it) }
        if (hasSelfHarm) {
            matchedCategories.add("SELF_HARM_DISTRESS")
            return SafetyScanResult(
                threatLevel = ThreatLevel.CRITICAL,
                matchedCategories = matchedCategories,
                riskScore = 0.99f,
                recommendedAction = SafetyAction.EMERGENCY_INTERCEPT,
                guidanceText = "You are not alone. Help is right here. Please reach out to our counsellor or emergency helpline (1098)."
            )
        }

        // 2. Extortion / Blackmail
        val hasExtortion = extortionKeywords.any { lower.contains(it) }
        if (hasExtortion) {
            matchedCategories.add("EXTORTION_PHOTO_COERCION")
            score += 0.55f
        }

        // 3. Secrecy & Grooming
        val hasSecrecy = secrecyKeywords.any { lower.contains(it) }
        if (hasSecrecy) {
            matchedCategories.add("SECRECY_COERCION")
            score += 0.35f
        }

        val hasGrooming = groomingKeywords.any { lower.contains(it) }
        if (hasGrooming) {
            matchedCategories.add("OFFLINE_MEETING_SOLICITATION")
            score += 0.40f
        }

        val threatLevel = when {
            score >= 0.75f -> ThreatLevel.HIGH_RISK
            score >= 0.35f -> ThreatLevel.SUSPICIOUS
            else -> ThreatLevel.SAFE
        }

        val action = when (threatLevel) {
            ThreatLevel.HIGH_RISK -> SafetyAction.SHOW_DECOY_EXIT
            ThreatLevel.SUSPICIOUS -> SafetyAction.ADVICE_CHIP
            else -> SafetyAction.NONE
        }

        val guidance = when (threatLevel) {
            ThreatLevel.HIGH_RISK -> "Warning: Suspicious blackmail or private photo demand detected. Remember: this is NOT your fault. Do NOT send anything."
            ThreatLevel.SUSPICIOUS -> "Safety Tip: Never share personal details, passwords, or agree to secret meetings alone."
            else -> "Message checked and safe."
        }

        return SafetyScanResult(
            threatLevel = threatLevel,
            matchedCategories = matchedCategories,
            riskScore = score.coerceAtMost(1.0f),
            recommendedAction = action,
            guidanceText = guidance
        )
    }

    /**
     * Scans text extracted via OCR from screenshots (Instagram, WhatsApp, Discord, etc.).
     */
    fun scanScreenshotOcrText(extractedText: String): SafetyScanResult {
        Timber.d("Analyzing OCR screenshot text of length %d", extractedText.length)
        return scanText(extractedText)
    }

    /**
     * Verifies whether on-device ONNX runtime engine is operational.
     */
    fun isEdgeEngineAvailable(): Boolean {
        return try {
            Class.forName("ai.onnxruntime.OrtEnvironment")
            true
        } catch (e: ClassNotFoundException) {
            false
        }
    }
}
