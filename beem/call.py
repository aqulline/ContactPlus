from jnius import autoclass
from jnius import cast
from android.runnable import run_on_ui_thread
from kivy.clock import Clock


# "android.permission.CALL_PHONE"

class Actions:
    url = ""
    webview = None

    @run_on_ui_thread
    def call(self, num):
        Intent = autoclass('android.content.Intent')
        Uri = autoclass('android.net.Uri')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        intent = Intent(Intent.ACTION_CALL)
        intent.setData(Uri.parse("tel:" + num))
        currentActivity = cast('android.app.Activity',
                               PythonActivity.mActivity)
        currentActivity.startActivity(intent)