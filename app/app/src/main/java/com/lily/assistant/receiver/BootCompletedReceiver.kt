package com.lily.assistant.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import com.lily.assistant.service.HotwordForegroundService

class BootCompletedReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val action = intent.action ?: return
        if (action == Intent.ACTION_BOOT_COMPLETED || action == Intent.ACTION_LOCKED_BOOT_COMPLETED) {
            context.startForegroundService(Intent(context, HotwordForegroundService::class.java))
        }
    }
}
