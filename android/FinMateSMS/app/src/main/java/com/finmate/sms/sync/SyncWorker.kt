package com.finmate.sms.sync

import android.content.Context
import android.util.Log
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.finmate.sms.data.AppDatabase
import com.finmate.sms.data.PendingTransaction
import com.finmate.sms.data.PreferencesManager
import java.io.IOException

class SyncWorker(
    appContext: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        val database = AppDatabase.getInstance(applicationContext)
        val dao = database.pendingTransactionDao()
        val prefs = PreferencesManager(applicationContext)

        val pendingList = dao.getPendingTransactions()
        if (pendingList.isEmpty()) {
            return Result.success()
        }

        val apiService = try {
            NetworkClient.getApiService(applicationContext)
        } catch (e: Exception) {
            Log.e(TAG, "Error initializing network client", e)
            return Result.retry()
        }

        var hasNetworkFailure = false

        for (tx in pendingList) {
            dao.updateSyncStatus(tx.localId, PendingTransaction.STATUS_SYNCING, System.currentTimeMillis(), null)

            val request = SmsTransactionRequest(
                amount = tx.amount,
                transactionDate = tx.transactionDate,
                type = tx.type,
                category = tx.category,
                description = tx.description,
                source = tx.source,
                sender = tx.sender,
                smsHash = tx.smsHash
            )

            try {
                val response = apiService.createTransactionFromSms(request)
                if (response.isSuccessful || response.code() == 409) {
                    // 201 Created or 409 Conflict (Duplicate already exists on server) -> Synced!
                    dao.updateSyncStatus(
                        id = tx.localId,
                        status = PendingTransaction.STATUS_SYNCED,
                        attemptTime = System.currentTimeMillis(),
                        error = if (response.code() == 409) "Already recorded on server" else null
                    )
                    prefs.lastSyncTimestamp = System.currentTimeMillis()
                    Log.i(TAG, "Successfully synchronized transaction ${tx.localId} (HTTP ${response.code()})")
                } else {
                    // Server validation or business error (4xx / 5xx)
                    val errorMsg = "HTTP ${response.code()}: ${response.errorBody()?.string()}"
                    dao.updateSyncStatus(
                        id = tx.localId,
                        status = PendingTransaction.STATUS_FAILED,
                        attemptTime = System.currentTimeMillis(),
                        error = errorMsg
                    )
                    Log.w(TAG, "Failed synchronizing transaction ${tx.localId}: $errorMsg")
                }
            } catch (e: IOException) {
                // Network unavailable or connection timed out - keep as pending for retry
                hasNetworkFailure = true
                dao.updateSyncStatus(
                    id = tx.localId,
                    status = PendingTransaction.STATUS_PENDING,
                    attemptTime = System.currentTimeMillis(),
                    error = "Network offline: ${e.message}"
                )
                Log.w(TAG, "Network unavailable while syncing transaction ${tx.localId}, will retry: ${e.message}")
            } catch (e: Exception) {
                // Unexpected error
                dao.updateSyncStatus(
                    id = tx.localId,
                    status = PendingTransaction.STATUS_FAILED,
                    attemptTime = System.currentTimeMillis(),
                    error = "Unexpected error: ${e.message}"
                )
                Log.e(TAG, "Unexpected error synchronizing transaction ${tx.localId}", e)
            }
        }

        return if (hasNetworkFailure) Result.retry() else Result.success()
    }

    companion object {
        private const val TAG = "FinMateSyncWorker"
        const val WORK_NAME = "finmate_sms_sync_work"

        /**
         * Enqueues a sync task that runs as soon as internet connectivity is available.
         */
        fun enqueue(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val syncRequest = OneTimeWorkRequestBuilder<SyncWorker>()
                .setConstraints(constraints)
                .build()

            WorkManager.getInstance(context)
                .enqueueUniqueWork(
                    WORK_NAME,
                    ExistingWorkPolicy.REPLACE,
                    syncRequest
                )
        }
    }
}
