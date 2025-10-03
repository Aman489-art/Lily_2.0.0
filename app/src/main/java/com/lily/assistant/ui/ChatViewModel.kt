package com.lily.assistant.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.viewModelScope
import com.lily.assistant.model.ChatMessage
import com.lily.assistant.repo.LilyRepository
import com.lily.assistant.tts.TtsManager
import com.lily.assistant.data.room.AppDatabase
import com.lily.assistant.data.room.ChatMessageEntity
import com.lily.assistant.system.CommandExecutor
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class ChatViewModel(app: Application) : AndroidViewModel(app) {
    private val repository = LilyRepository(app)
    private val tts = TtsManager(app)
    private val db = AppDatabase.get(app)
    private val executor = CommandExecutor(app)

    private val _messages = MutableLiveData<List<ChatMessage>>(emptyList())
    val messages: LiveData<List<ChatMessage>> = _messages

    private var nextId: Long = 1

    init {
        viewModelScope.launch(Dispatchers.IO) {
            val history = db.chatDao().getAll().map {
                ChatMessage(id = it.id, text = it.text, isUser = it.isUser, timestampMs = it.timestamp)
            }
            nextId = (history.maxOfOrNull { it.id } ?: 0L) + 1
            withContext(Dispatchers.Main) { _messages.value = history }
        }
    }

    fun sendUserMessage(text: String) {
        if (text.isBlank()) return
        val userMsg = ChatMessage(id = nextId++, text = text, isUser = true)
        appendAndPersist(userMsg)

        // Local command handling first
        viewModelScope.launch(Dispatchers.IO) {
            val localHandled = executor.tryHandle(text)
            if (localHandled != null) {
                val botMsg = ChatMessage(id = nextId++, text = localHandled, isUser = false)
                appendAndPersist(botMsg, speak = true)
                return@launch
            }

            val reply = try {
                repository.send(text)
            } catch (e: Exception) {
                "Sorry, I couldn't reach the server."
            }
            val botMsg = ChatMessage(id = nextId++, text = reply, isUser = false)
            appendAndPersist(botMsg, speak = true)
        }
    }

    private fun appendAndPersist(message: ChatMessage, speak: Boolean = false) {
        _messages.postValue((_messages.value ?: emptyList()) + message)
        viewModelScope.launch(Dispatchers.IO) {
            db.chatDao().insert(ChatMessageEntity(
                id = message.id,
                text = message.text,
                isUser = message.isUser,
                timestamp = message.timestampMs
            ))
        }
        if (!message.isUser && speak) tts.speak(message.text)
    }

    override fun onCleared() {
        super.onCleared()
        tts.shutdown()
    }
}
