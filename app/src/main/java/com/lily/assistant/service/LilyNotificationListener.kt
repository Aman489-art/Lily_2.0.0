package com.lily.assistant.service

import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification

class LilyNotificationListener : NotificationListenerService() {
    override fun onListenerConnected() {
        super.onListenerConnected()
    }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        // Future: could read aloud notifications based on user command
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification?) {
    }
}
