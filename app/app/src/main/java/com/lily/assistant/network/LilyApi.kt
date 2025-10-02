package com.lily.assistant.network

import retrofit2.http.Body
import retrofit2.http.Header
import retrofit2.http.POST

interface LilyApi {
    @POST("/lily")
    suspend fun sendQuery(
        @Header("x-api-key") apiKey: String,
        @Body request: LilyRequest
    ): LilyResponse
}

data class LilyRequest(
    val text: String,
    val language: String? = null,
    val sessionId: String? = null
)

data class LilyResponse(
    val reply: String,
    val metadata: Map<String, String>? = null
)
