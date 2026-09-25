package com.finmate.sms.sync

import android.content.Context
import com.finmate.sms.data.PreferencesManager
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object NetworkClient {

    private var currentBaseUrl: String? = null
    private var cachedApiService: FinMateApiService? = null

    fun getApiService(context: Context): FinMateApiService {
        val prefs = PreferencesManager(context)
        val baseUrl = prefs.serverBaseUrl.trimEnd('/') + "/"

        if (cachedApiService != null && currentBaseUrl == baseUrl) {
            return cachedApiService!!
        }

        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }

        val okHttpClient = OkHttpClient.Builder()
            .addInterceptor(loggingInterceptor)
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .writeTimeout(15, TimeUnit.SECONDS)
            .build()

        val retrofit = Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        currentBaseUrl = baseUrl
        val service = retrofit.create(FinMateApiService::class.java)
        cachedApiService = service
        return service
    }

    fun invalidate() {
        cachedApiService = null
        currentBaseUrl = null
    }
}
