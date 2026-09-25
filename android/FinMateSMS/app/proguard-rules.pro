# Add project specific ProGuard rules here.
-keepclassmembers class * {
    @androidx.room.Entity *;
    @androidx.room.Dao *;
}
-keep class com.finmate.sms.sync.** { *; }
