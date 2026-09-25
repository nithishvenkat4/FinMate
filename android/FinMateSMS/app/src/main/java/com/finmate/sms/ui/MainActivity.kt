package com.finmate.sms.ui

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.ImageButton
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.finmate.sms.R
import com.finmate.sms.data.AppDatabase
import com.finmate.sms.data.PendingTransaction
import com.finmate.sms.data.PreferencesManager
import com.finmate.sms.sync.SyncWorker
import com.google.android.material.switchmaterial.SwitchMaterial

class MainActivity : AppCompatActivity() {

    private lateinit var prefs: PreferencesManager
    private lateinit var db: AppDatabase
    private lateinit var adapter: TransactionAdapter

    private lateinit var switchTracking: SwitchMaterial
    private lateinit var tvCountSynced: TextView
    private lateinit var tvCountPending: TextView
    private lateinit var tvCountFailed: TextView
    private lateinit var tvAllowedSendersSummary: TextView
    private lateinit var tvEmptyState: TextView
    private lateinit var rvTransactions: RecyclerView
    private lateinit var btnSyncNow: Button
    private lateinit var btnOpenSettings: ImageButton

    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted: Boolean ->
        if (isGranted) {
            Toast.makeText(this, "SMS permission granted", Toast.LENGTH_SHORT).show()
        } else {
            Toast.makeText(
                this,
                "SMS permission is required to detect financial transactions",
                Toast.LENGTH_LONG
            ).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        prefs = PreferencesManager(this)
        db = AppDatabase.getInstance(this)

        initViews()
        setupRecyclerView()
        setupListeners()
        observeData()
        checkPermissions()
    }

    private fun initViews() {
        switchTracking = findViewById(R.id.switchTracking)
        tvCountSynced = findViewById(R.id.tvCountSynced)
        tvCountPending = findViewById(R.id.tvCountPending)
        tvCountFailed = findViewById(R.id.tvCountFailed)
        tvAllowedSendersSummary = findViewById(R.id.tvAllowedSendersSummary)
        tvEmptyState = findViewById(R.id.tvEmptyState)
        rvTransactions = findViewById(R.id.rvTransactions)
        btnSyncNow = findViewById(R.id.btnSyncNow)
        btnOpenSettings = findViewById(R.id.btnOpenSettings)

        switchTracking.isChecked = prefs.isTrackingEnabled
        tvAllowedSendersSummary.text = prefs.getAllowedSendersCommaSeparated()
    }

    private fun setupRecyclerView() {
        adapter = TransactionAdapter()
        rvTransactions.layoutManager = LinearLayoutManager(this)
        rvTransactions.adapter = adapter
    }

    private fun setupListeners() {
        switchTracking.setOnCheckedChangeListener { _, isChecked ->
            prefs.isTrackingEnabled = isChecked
            val statusStr = if (isChecked) "enabled" else "disabled"
            Toast.makeText(this, "SMS Transaction Tracking $statusStr", Toast.LENGTH_SHORT).show()
        }

        btnSyncNow.setOnClickListener {
            Toast.makeText(this, "Initiating synchronization...", Toast.LENGTH_SHORT).show()
            SyncWorker.enqueue(this)
        }

        btnOpenSettings.setOnClickListener {
            SettingsDialog.show(this) {
                tvAllowedSendersSummary.text = prefs.getAllowedSendersCommaSeparated()
            }
        }
    }

    private fun observeData() {
        // Observe full transaction history
        db.pendingTransactionDao().getAllTransactionsLiveData().observe(this) { list ->
            adapter.submitList(list)
            tvEmptyState.visibility = if (list.isNullOrEmpty()) View.VISIBLE else View.GONE
        }

        // Observe metrics counters
        db.pendingTransactionDao().getCountByStatusLiveData(PendingTransaction.STATUS_SYNCED)
            .observe(this) { count ->
                tvCountSynced.text = (count ?: 0).toString()
            }

        db.pendingTransactionDao().getCountByStatusLiveData(PendingTransaction.STATUS_PENDING)
            .observe(this) { count ->
                tvCountPending.text = (count ?: 0).toString()
            }

        db.pendingTransactionDao().getCountByStatusLiveData(PendingTransaction.STATUS_FAILED)
            .observe(this) { count ->
                tvCountFailed.text = (count ?: 0).toString()
            }
    }

    private fun checkPermissions() {
        if (ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.RECEIVE_SMS
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissionLauncher.launch(Manifest.permission.RECEIVE_SMS)
        }
    }
}
