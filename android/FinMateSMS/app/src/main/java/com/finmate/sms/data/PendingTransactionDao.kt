package com.finmate.sms.data

import androidx.lifecycle.LiveData
import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update

@Dao
interface PendingTransactionDao {

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insert(transaction: PendingTransaction): Long

    @Query("SELECT * FROM pending_transactions WHERE sync_status IN ('PENDING', 'FAILED') ORDER BY created_at ASC")
    suspend fun getPendingTransactions(): List<PendingTransaction>

    @Query("SELECT * FROM pending_transactions ORDER BY created_at DESC")
    fun getAllTransactionsLiveData(): LiveData<List<PendingTransaction>>

    @Query("SELECT * FROM pending_transactions ORDER BY created_at DESC")
    suspend fun getAllTransactions(): List<PendingTransaction>

    @Query("SELECT * FROM pending_transactions WHERE sms_hash = :hash LIMIT 1")
    suspend fun getByHash(hash: String): PendingTransaction?

    @Query("UPDATE pending_transactions SET sync_status = :status, last_sync_attempt = :attemptTime, sync_error = :error WHERE local_id = :id")
    suspend fun updateSyncStatus(id: Long, status: String, attemptTime: Long, error: String?)

    @Query("SELECT COUNT(*) FROM pending_transactions WHERE sync_status = :status")
    fun getCountByStatusLiveData(status: String): LiveData<Int>

    @Query("SELECT COUNT(*) FROM pending_transactions WHERE sync_status = :status")
    suspend fun getCountByStatus(status: String): Int

    @Update
    suspend fun update(transaction: PendingTransaction)

    @Query("DELETE FROM pending_transactions")
    suspend fun clearAll()
}
