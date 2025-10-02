package com.lily.assistant.service

import android.accessibilityservice.AccessibilityService
import android.view.accessibility.AccessibilityEvent

class LilyAccessibilityService : AccessibilityService() {
    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        // Future: react to events for app opening or UI automation
    }

    override fun onInterrupt() {
    }
}
