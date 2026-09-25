package com.finmate.sms.sync

import com.google.gson.annotations.SerializedName
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

data class SmsTransactionRequest(
    @SerializedName("amount")
    val amount: Double,

    @SerializedName("transaction_date")
    val transactionDate: String,

    @SerializedName("type")
    val type: String,

    @SerializedName("category")
    val category: String = "Other",

    @SerializedName("description")
    val description: String = "SMS Transaction",

    @SerializedName("source")
    val source: String = "sms",

    @SerializedName("sender")
    val sender: String,

    @SerializedName("sms_hash")
    val smsHash: String
)

data class TransactionResponseDto(
    @SerializedName("id")
    val id: String,

    @SerializedName("amount")
    val amount: String,

    @SerializedName("transaction_type")
    val transactionType: String,

    @SerializedName("category")
    val category: String,

    @SerializedName("description")
    val description: String,

    @SerializedName("source_type")
    val sourceType: String?,

    @SerializedName("source_reference")
    val sourceReference: String?
)

interface FinMateApiService {

    @POST("/api/v1/transactions/from-sms")
    suspend fun createTransactionFromSms(
        @Body request: SmsTransactionRequest
    ): Response<TransactionResponseDto>
}
