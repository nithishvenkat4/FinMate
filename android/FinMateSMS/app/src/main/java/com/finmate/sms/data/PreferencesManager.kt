package com.finmate.sms.data

import android.content.Context
import android.content.SharedPreferences

class PreferencesManager(context: Context) {

    private val prefs: SharedPreferences =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    var isTrackingEnabled: Boolean
        get() = prefs.getBoolean(KEY_TRACKING_ENABLED, true)
        set(value) = prefs.edit().putBoolean(KEY_TRACKING_ENABLED, value).apply()

    var serverBaseUrl: String
        get() = prefs.getString(KEY_SERVER_URL, DEFAULT_SERVER_URL) ?: DEFAULT_SERVER_URL
        set(value) = prefs.edit().putString(KEY_SERVER_URL, value.trimEnd('/')).apply()

    var allowedSenders: Set<String>
        get() {
            val saved = prefs.getStringSet(KEY_ALLOWED_SENDERS, null)
            return saved ?: DEFAULT_SENDERS
        }
        set(value) = prefs.edit().putStringSet(KEY_ALLOWED_SENDERS, value).apply()

    var lastSyncTimestamp: Long
        get() = prefs.getLong(KEY_LAST_SYNC, 0L)
        set(value) = prefs.edit().putLong(KEY_LAST_SYNC, value).apply()

    fun isSenderAllowed(rawSender: String): Boolean {
        if (!isTrackingEnabled) return false
        val cleanSender = rawSender.uppercase().replace(Regex("[^A-Z0-9]"), "")
        return allowedSenders.any { allowed ->
            val cleanAllowed = allowed.uppercase().trim()
            cleanSender.contains(cleanAllowed) || cleanAllowed.contains(cleanSender)
        }
    }

    fun getAllowedSendersCommaSeparated(): String {
        return allowedSenders.joinToString(", ")
    }

    fun setAllowedSendersFromCommaSeparated(csv: String) {
        val senders = csv.split(",")
            .map { it.trim().uppercase() }
            .filter { it.isNotEmpty() }
            .toSet()
        if (senders.isNotEmpty()) {
            allowedSenders = senders
        }
    }

    companion object {
        private const val PREFS_NAME = "finmate_sms_prefs"
        private const val KEY_TRACKING_ENABLED = "tracking_enabled"
        private const val KEY_SERVER_URL = "server_url"
        private const val KEY_ALLOWED_SENDERS = "allowed_senders"
        private const val KEY_LAST_SYNC = "last_sync"

        const val DEFAULT_SERVER_URL = "http://10.0.2.2:8000"

        val DEFAULT_SENDERS = setOf(
            "HDFCBK",
            "SBIINB",
            "ICICIB",
            "AXISBK",
            "KOTAKB",
            "PAYTM",
            "CANBNK",
            "PUNBNK",
            "YESBNK",
            "UNIONB"
        )
    }
}
