package com.lily.assistant.ui

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.inputmethod.EditorInfo
import android.widget.ImageButton
import android.widget.ImageView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.lifecycle.Observer
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.textfield.TextInputEditText
import com.lily.assistant.R
import com.lily.assistant.export.ExportUtils
import com.lily.assistant.service.HotwordForegroundService

class MainActivity : AppCompatActivity() {
    private val viewModel: ChatViewModel by viewModels()

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        ensurePermissions()
        ensureOverlayPermission()
        startForegroundListening()

        val recycler = findViewById<RecyclerView>(R.id.recyclerView)
        val input = findViewById<TextInputEditText>(R.id.inputEditText)
        val send = findViewById<ImageButton>(R.id.sendButton)
        val mic = findViewById<ImageButton>(R.id.micButton)
        val settings = findViewById<ImageView>(R.id.settingsButton)

        val adapter = ChatAdapter()
        recycler.adapter = adapter
        recycler.layoutManager = LinearLayoutManager(this).apply { stackFromEnd = true }

        viewModel.messages.observe(this, Observer {
            adapter.submitList(it)
            recycler.scrollToPosition(adapter.itemCount - 1)
        })

        send.setOnClickListener {
            val text = input.text?.toString().orEmpty()
            viewModel.sendUserMessage(text)
            input.setText("")
        }

        input.setOnEditorActionListener { _, actionId, _ ->
            if (actionId == EditorInfo.IME_ACTION_SEND) {
                send.performClick(); true
            } else false
        }

        mic.setOnClickListener {
            Toast.makeText(this, "Mic activation coming soon", Toast.LENGTH_SHORT).show()
        }

        settings.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }
        settings.setOnLongClickListener {
            ExportUtils.exportLatestToShare(this, viewModel.messages.value ?: emptyList())
            true
        }
    }

    private fun ensurePermissions() {
        val perms = mutableListOf(Manifest.permission.RECORD_AUDIO)
        if (Build.VERSION.SDK_INT >= 33) {
            perms.add(Manifest.permission.POST_NOTIFICATIONS)
        }
        val need = perms.filter {
            ActivityCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }
        if (need.isNotEmpty()) permissionLauncher.launch(need.toTypedArray())
    }

    private fun ensureOverlayPermission() {
        if (!Settings.canDrawOverlays(this)) {
            val intent = Intent(
                Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                Uri.parse("package:" + packageName)
            )
            startActivity(intent)
        }
    }

    private fun startForegroundListening() {
        val intent = Intent(this, HotwordForegroundService::class.java)
        if (Build.VERSION.SDK_INT >= 26) startForegroundService(intent) else startService(intent)
    }
}
