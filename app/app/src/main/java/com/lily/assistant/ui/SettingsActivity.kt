package com.lily.assistant.ui

import android.os.Bundle
import android.widget.Button
import com.google.android.material.textfield.TextInputEditText
import androidx.appcompat.app.AppCompatActivity
import com.lily.assistant.R
import com.lily.assistant.data.SecurePrefs

class SettingsActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        val prefs = SecurePrefs(this)
        val baseUrl = findViewById<TextInputEditText>(R.id.baseUrlInput)
        val apiKey = findViewById<TextInputEditText>(R.id.apiKeyInput)
        val save = findViewById<Button>(R.id.saveButton)

        baseUrl.setText(prefs.getBaseUrl())
        apiKey.setText(prefs.getApiKey())

        save.setOnClickListener {
            prefs.setBaseUrl(baseUrl.text?.toString().orEmpty())
            prefs.setApiKey(apiKey.text?.toString().orEmpty())
            finish()
        }
    }
}
