package com.finmate.sms.ui

import android.app.AlertDialog
import android.content.Context
import android.view.LayoutInflater
import android.widget.EditText
import android.widget.Toast
import com.finmate.sms.R
import com.finmate.sms.data.PreferencesManager
import com.finmate.sms.sync.NetworkClient

object SettingsDialog {

    fun show(context: Context, onSaved: () -> Unit) {
        val prefs = PreferencesManager(context)
        val dialogView = LayoutInflater.from(context).inflate(R.layout.dialog_settings, null)

        val etServerUrl = dialogView.findViewById<EditText>(R.id.etServerUrl)
        val etAllowedSenders = dialogView.findViewById<EditText>(R.id.etAllowedSenders)

        etServerUrl.setText(prefs.serverBaseUrl)
        etAllowedSenders.setText(prefs.getAllowedSendersCommaSeparated())

        AlertDialog.Builder(context)
            .setView(dialogView)
            .setPositiveButton("Save") { dialog, _ ->
                val newUrl = etServerUrl.text.toString().trim()
                val newSenders = etAllowedSenders.text.toString().trim()

                if (newUrl.isNotEmpty()) {
                    prefs.serverBaseUrl = newUrl
                    NetworkClient.invalidate()
                }

                if (newSenders.isNotEmpty()) {
                    prefs.setAllowedSendersFromCommaSeparated(newSenders)
                }

                Toast.makeText(context, "Settings updated successfully", Toast.LENGTH_SHORT).show()
                onSaved()
                dialog.dismiss()
            }
            .setNegativeButton("Cancel") { dialog, _ ->
                dialog.dismiss()
            }
            .create()
            .show()
    }
}
