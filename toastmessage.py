import time
from win10toast import ToastNotifier

# one-time initialization
toaster = ToastNotifier()

# show notification whenever needed
toaster.show_toast("Brenda", "It's time to change your passwords . . .",
                   threaded=True, icon_path='brenda.ico', duration=60)  # in seconds

# To check if any notifications are active, use 'toaster.notification_active()'
# wait for threaded notification to finish
while toaster.notification_active():
    time.sleep(0.1)
