package com.finmate.sms.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import android.util.Log
import com.finmate.sms.data.AppDatabase
import com.finmate.sms.data.PendingTransaction
import com.finmate.sms.data.PreferencesManager
import com.finmate.sms.parser.SmsTransactionParser
import com.finmate.sms.sync.SyncWorker
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class SmsReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action != Telephony.Sms.Intents.SMS_RECEIVED_ACTION) {
            return
        }

        val prefs = PreferencesManager(context)
        if (!prefs.isTrackingEnabled) {
            Log.d(TAG, "SMS tracking is disabled by user. Ignoring incoming SMS.")
            return
        }

        val messages = Telephony.Sms.Intents.getMessagesFromIntent(intent) ?: return
        if (messages.isEmpty()) return

        // Group multipart SMS messages by originating address
        val messagesBySender = messages.groupBy { it.displayOriginatingAddress ?: it.originatingAddress ?: "" }

        for ((sender, parts) in messagesBySender) {
            if (sender.isBlank()) continue

            // 1. Allowed Financial Sender Filter
            if (!prefs.isSenderAllowed(sender)) {
                Log.d(TAG, "Ignoring SMS from non-allowed sender: $sender")
                continue
            }

            val fullBody = parts.joinToString("") { it.displayMessageBody ?: it.messageBody ?: "" }
            val timestamp = parts.firstOrNull()?.timestampMillis ?: System.currentTimeMillis()

            Log.i(TAG, "Processing incoming financial SMS from allowed sender: $sender")

            // 2. Parse SMS Transaction Locally
            val parsed = SmsTransactionParser.parse(
                sender = sender,
                messageBody = fullBody,
                receivedTimestamp = timestamp
            )

            if (parsed == null) {
                Log.w(TAG, "Could not extract valid financial transaction from SMS from $sender. Discarding.")
                continue
            }

            // 3. Store into local Room Offline Queue and Trigger Auto-Sync
            val pendingTx = PendingTransaction(
                amount = parsed.amount,
                transactionDate = parsed.transactionDate,
                type = parsed.type,
                category = parsed.category,
                description = parsed.description,
                source = parsed.source,
                sender = parsed.sender,
                smsHash = parsed.smsHash,
                syncStatus = PendingTransaction.STATUS_PENDING,
                createdAt = System.currentTimeMillis()
            )

            val pendingResult = goAsync()
            CoroutineScope(Dispatchers.IO).launch {
                try {
                    val db = AppDatabase.getInstance(context)
                    val insertedId = db.pendingTransactionDao().insert(pendingTx)

                    if (insertedId > 0) {
                        Log.i(TAG, "Enqueued new SMS transaction #$insertedId locally. Scheduling sync.")
                        // Automatically synchronize if internet is available, or queue for when connected
                        SyncWorker.enqueue(context)
                    } else {
                        Log.w(TAG, "Duplicate SMS ignored locally based on unique hash: ${parsed.smsHash}")
                    }
                } catch (e: Exception) {
                    Log.e(TAG, "Error storing pending transaction", e)
                } finally {
                    pendingResult.finish()
                }
            }
        }
    }

    companion object {
        private const val TAG = "FinMateSmsReceiver"
    }
}
