package com.lily.assistant.repo

import android.content.Context
import com.lily.assistant.data.SecurePrefs
import com.lily.assistant.network.LilyRequest
import com.lily.assistant.network.RetrofitProvider

class LilyRepository(private val appContext: Context) {
    private val securePrefs = SecurePrefs(appContext)

    suspend fun send(text: String, language: String? = null, sessionId: String? = null): String {
        val api = RetrofitProvider.getApi(appContext, securePrefs.getBaseUrl())
        val response = api.sendQuery(
            apiKey = securePrefs.getApiKey(),
            request = LilyRequest(text = text, language = language, sessionId = sessionId)
        )
        return response.reply
    }
}
