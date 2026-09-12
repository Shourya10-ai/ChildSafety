package com.childsafety.app.security

import android.view.KeyEvent

object DuressKeyTrigger {
    private const val REQUIRED_PRESSES = 3
    private const val TIME_WINDOW_MS = 2000L

    private val pressTimestamps = mutableListOf<Long>()
    private var duressCallback: (() -> Unit)? = null

    fun setCallback(callback: () -> Unit) {
        duressCallback = callback
    }

    fun handleKeyEvent(keyCode: Int): Boolean {
        if (keyCode == KeyEvent.KEYCODE_VOLUME_DOWN) {
            val now = System.currentTimeMillis()
            pressTimestamps.add(now)

            // Remove timestamps older than the sliding time window
            pressTimestamps.removeAll { now - it > TIME_WINDOW_MS }

            if (pressTimestamps.size >= REQUIRED_PRESSES) {
                pressTimestamps.clear()
                duressCallback?.invoke()
                return true
            }
        }
        return false
    }
}
