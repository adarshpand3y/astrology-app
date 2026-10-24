package expo.modules.exactalarms

import android.app.AlarmManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import expo.modules.kotlin.exception.Exceptions
import expo.modules.kotlin.modules.Module
import expo.modules.kotlin.modules.ModuleDefinition

// Whether this app may schedule exact alarms, and a shortcut to the setting that allows it.
// expo-notifications uses exact alarms only when this is true; otherwise Android batches
// scheduled notifications and, while the phone is idle, holds them back.
class ExactAlarmsModule : Module() {
  private val context: Context
    get() = appContext.reactContext ?: throw Exceptions.ReactContextLost()

  override fun definition() = ModuleDefinition {
    Name("ExactAlarms")

    Function("canScheduleExactAlarms") {
      if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) {
        true // no special permission before Android 12
      } else {
        (context.getSystemService(Context.ALARM_SERVICE) as AlarmManager).canScheduleExactAlarms()
      }
    }

    // Opens this app's "Alarms & reminders" page. Returns false where there is no such page.
    AsyncFunction("openSettingsAsync") {
      if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) {
        false
      } else {
        val intent = Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM, Uri.parse("package:${context.packageName}"))
          .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
        true
      }
    }
  }
}
