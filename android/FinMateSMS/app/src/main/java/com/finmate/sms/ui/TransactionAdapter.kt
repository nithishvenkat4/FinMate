package com.finmate.sms.ui

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.core.content.ContextCompat
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.finmate.sms.R
import com.finmate.sms.data.PendingTransaction
import java.text.NumberFormat
import java.util.Locale

class TransactionAdapter :
    ListAdapter<PendingTransaction, TransactionAdapter.TransactionViewHolder>(DiffCallback) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): TransactionViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_transaction, parent, false)
        return TransactionViewHolder(view)
    }

    override fun onBindViewHolder(holder: TransactionViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class TransactionViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvSender: TextView = itemView.findViewById(R.id.tvSender)
        private val tvDate: TextView = itemView.findViewById(R.id.tvDate)
        private val tvAmount: TextView = itemView.findViewById(R.id.tvAmount)
        private val tvDescription: TextView = itemView.findViewById(R.id.tvDescription)
        private val tvStatus: TextView = itemView.findViewById(R.id.tvStatus)
        private val tvError: TextView = itemView.findViewById(R.id.tvError)

        fun bind(item: PendingTransaction) {
            tvSender.text = item.sender
            tvDate.text = item.transactionDate
            tvDescription.text = "${item.description} • ${item.category}"

            val inrFormat = NumberFormat.getCurrencyInstance(Locale("en", "IN"))
            val formattedAmount = inrFormat.format(item.amount)

            if (item.type.lowercase(Locale.ROOT) == "income") {
                tvAmount.text = "+$formattedAmount"
                tvAmount.setTextColor(ContextCompat.getColor(itemView.context, R.color.status_synced))
            } else {
                tvAmount.text = "-$formattedAmount"
                tvAmount.setTextColor(ContextCompat.getColor(itemView.context, R.color.text_primary))
            }

            tvStatus.text = item.syncStatus

            when (item.syncStatus) {
                PendingTransaction.STATUS_SYNCED -> {
                    tvStatus.setTextColor(ContextCompat.getColor(itemView.context, R.color.status_synced))
                    tvError.visibility = View.GONE
                }
                PendingTransaction.STATUS_PENDING -> {
                    tvStatus.setTextColor(ContextCompat.getColor(itemView.context, R.color.status_pending))
                    tvError.visibility = View.GONE
                }
                PendingTransaction.STATUS_SYNCING -> {
                    tvStatus.setTextColor(ContextCompat.getColor(itemView.context, R.color.status_syncing))
                    tvError.visibility = View.GONE
                }
                PendingTransaction.STATUS_FAILED -> {
                    tvStatus.setTextColor(ContextCompat.getColor(itemView.context, R.color.status_failed))
                    if (!item.syncError.isNullOrBlank()) {
                        tvError.text = item.syncError
                        tvError.visibility = View.VISIBLE
                    } else {
                        tvError.visibility = View.GONE
                    }
                }
            }
        }
    }

    companion object DiffCallback : DiffUtil.ItemCallback<PendingTransaction>() {
        override fun areItemsTheSame(oldItem: PendingTransaction, newItem: PendingTransaction): Boolean {
            return oldItem.localId == newItem.localId
        }

        override fun areContentsTheSame(oldItem: PendingTransaction, newItem: PendingTransaction): Boolean {
            return oldItem == newItem
        }
    }
}
