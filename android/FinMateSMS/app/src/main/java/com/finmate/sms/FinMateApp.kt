package com.finmate.sms

import android.app.Application
import android.util.Log
import androidx.work.Configuration
import com.finmate.sms.data.AppDatabase
import com.finmate.sms.sync.SyncWorker

class FinMateApp : Application(), Configuration.Provider {

    override fun onCreate() {
        super.onCreate()
        Log.i(TAG, "Initializing FinMate SMS Application")
        // Warm up Room DB
        AppDatabase.getInstance(this)
        // Ensure pending sync is enqueued if network is available
        SyncWorker.enqueue(this)
    }

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setMinimumLoggingLevel(Log.INFO)
            .build()

    companion object {
        private const val TAG = "FinMateApp"
    }
}
