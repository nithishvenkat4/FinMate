package com.finmate.sms.data

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * Local offline queue entity for transactions captured from incoming SMS notifications.
 * Duplicate protection is enforced at the database level via a unique index on sms_hash.
 */
@Entity(
    tableName = "pending_transactions",
    indices = [
        Index(value = ["sms_hash"], unique = true),
        Index(value = ["sync_status"])
    ]
)
data class PendingTransaction(
    @PrimaryKey(autoGenerate = true)
    @ColumnInfo(name = "local_id")
    val localId: Long = 0,

    @ColumnInfo(name = "amount")
    val amount: Double,

    @ColumnInfo(name = "transaction_date")
    val transactionDate: String,

    @ColumnInfo(name = "type")
    val type: String, // "expense" or "income"

    @ColumnInfo(name = "category")
    val category: String = "Other",

    @ColumnInfo(name = "description")
    val description: String = "SMS Transaction",

    @ColumnInfo(name = "source")
    val source: String = "sms",

    @ColumnInfo(name = "sender")
    val sender: String,

    @ColumnInfo(name = "sms_hash")
    val smsHash: String,

    @ColumnInfo(name = "sync_status")
    var syncStatus: String = STATUS_PENDING,

    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "last_sync_attempt")
    var lastSyncAttempt: Long? = null,

    @ColumnInfo(name = "sync_error")
    var syncError: String? = null
) {
    companion object {
        const val STATUS_PENDING = "PENDING"
        const val STATUS_SYNCING = "SYNCING"
        const val STATUS_SYNCED = "SYNCED"
        const val STATUS_FAILED = "FAILED"
    }
}
