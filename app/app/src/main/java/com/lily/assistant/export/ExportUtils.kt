package com.lily.assistant.export

import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.core.content.FileProvider
import com.lily.assistant.model.ChatMessage
import java.io.File

object ExportUtils {
    fun exportLatestToShare(context: Context, messages: List<ChatMessage>) {
        if (messages.isEmpty()) return
        val text = buildString {
            messages.forEach {
                append(if (it.isUser) "You: " else "Lily: ")
                append(it.text)
                append('\n')
            }
        }
        val cache = File(context.cacheDir, "exports").apply { mkdirs() }
        val out = File(cache, "lily_chat.txt")
        out.writeText(text)
        val uri: Uri = FileProvider.getUriForFile(context, context.packageName + ".provider", out)
        val intent = Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_STREAM, uri)
            putExtra(Intent.EXTRA_TEXT, text)
            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        }
        context.startActivity(Intent.createChooser(intent, "Share chat"))
    }
}
