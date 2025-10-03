package com.lily.assistant.system

import android.content.Context
import android.content.Intent
import android.media.AudioManager
import android.net.Uri
import android.provider.AlarmClock
import android.provider.Settings
import android.text.TextUtils
import android.widget.Toast
import androidx.core.content.ContextCompat
import java.util.Locale

class CommandExecutor(private val context: Context) {
    fun tryHandle(input: String): String? {
        val t = input.trim().lowercase(Locale.getDefault())
        return when {
            t.startsWith("turn wifi on") -> { toggleWifi(true); "Turning Wi-Fi on" }
            t.startsWith("turn wifi off") -> { toggleWifi(false); "Turning Wi-Fi off" }
            t.startsWith("turn bluetooth on") -> { toggleBluetooth(true); "Turning Bluetooth on" }
            t.startsWith("turn bluetooth off") -> { toggleBluetooth(false); "Turning Bluetooth off" }
            t.startsWith("increase volume") -> { adjustVolume(true); "Increasing volume" }
            t.startsWith("decrease volume") -> { adjustVolume(false); "Decreasing volume" }
            t.startsWith("set brightness") -> {
                val v = t.filter { it.isDigit() }.toIntOrNull()?.coerceIn(1, 255) ?: 128
                setBrightness(v); "Setting brightness"
            }
            t.startsWith("open ") -> {
                val appName = t.removePrefix("open ").trim()
                openApp(appName)
            }
            t.startsWith("set alarm") -> { setAlarmNow(); "Setting an alarm" }
            t.startsWith("set timer") -> { setTimer60(); "Starting a timer" }
            t.startsWith("send sms") -> { sendSmsTemplate(); "Opening SMS" }
            t.startsWith("send whatsapp") -> { sendWhatsAppTemplate(); "Opening WhatsApp" }
            else -> null
        }
    }

    private fun toggleWifi(enable: Boolean) {
        // Direct toggling is restricted on newer Android versions; show settings panel
        val intent = Intent(Settings.Panel.ACTION_INTERNET_CONNECTIVITY).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        Toast.makeText(context, "Please toggle Wi-Fi manually", Toast.LENGTH_SHORT).show()
    }

    private fun toggleBluetooth(enable: Boolean) {
        // On modern Android, direct toggle requires special privileges; open settings
        val intent = Intent(Settings.ACTION_BLUETOOTH_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        Toast.makeText(context, "Please toggle Bluetooth manually", Toast.LENGTH_SHORT).show()
    }

    private fun adjustVolume(up: Boolean) {
        val am = ContextCompat.getSystemService(context, AudioManager::class.java) ?: return
        val dir = if (up) AudioManager.ADJUST_RAISE else AudioManager.ADJUST_LOWER
        am.adjustStreamVolume(AudioManager.STREAM_MUSIC, dir, AudioManager.FLAG_SHOW_UI)
    }

    private fun setBrightness(value: Int) {
        try {
            Settings.System.putInt(context.contentResolver, Settings.System.SCREEN_BRIGHTNESS, value)
        } catch (_: SecurityException) {
            val i = Intent(Settings.ACTION_DISPLAY_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(i)
        }
    }

    private fun openApp(appName: String): String {
        val pm = context.packageManager
        val intent = pm.getLaunchIntentForPackage(appName)
        if (intent != null) {
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(intent)
            return "Opening $appName"
        }
        // Try by query on market name
        val i = Intent(Intent.ACTION_VIEW, Uri.parse("market://search?q=" + Uri.encode(appName)))
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(i)
        return "Couldn't find $appName; showing in Play Store"
    }

    private fun setAlarmNow() {
        val i = Intent(AlarmClock.ACTION_SET_ALARM)
            .putExtra(AlarmClock.EXTRA_MESSAGE, "Lily Alarm")
            .putExtra(AlarmClock.EXTRA_HOUR, 7)
            .putExtra(AlarmClock.EXTRA_MINUTES, 0)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        if (i.resolveActivity(context.packageManager) != null) context.startActivity(i)
    }

    private fun setTimer60() {
        val i = Intent(AlarmClock.ACTION_SET_TIMER)
            .putExtra(AlarmClock.EXTRA_LENGTH, 60)
            .putExtra(AlarmClock.EXTRA_MESSAGE, "Lily Timer")
            .putExtra(AlarmClock.EXTRA_SKIP_UI, false)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        if (i.resolveActivity(context.packageManager) != null) context.startActivity(i)
    }

    private fun sendSmsTemplate() {
        val i = Intent(Intent.ACTION_VIEW)
        i.data = Uri.parse("sms:")
        i.putExtra("sms_body", "Message from Lily")
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(i)
    }

    private fun sendWhatsAppTemplate() {
        val text = "Message from Lily"
        val i = Intent(Intent.ACTION_VIEW)
        i.data = Uri.parse("whatsapp://send?text=" + Uri.encode(text))
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(i)
    }
}
