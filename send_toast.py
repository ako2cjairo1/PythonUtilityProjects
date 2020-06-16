import time
from win10toast import ToastNotifier


class ToastMessage:
    def send_toast(self, title, message):
        # one-time initialization
        toaster = ToastNotifier()

        # show notification whenever needed
        toaster.show_toast(title=title, msg=message, threaded=True,
                           icon_path='brenda.ico', duration=15)  # in seconds

        # To check if any notifications are active, use 'toaster.notification_active()'
        # wait for threaded notification to finish
        while toaster.notification_active():
            time.sleep(0.1)


if __name__ == "__main__":
    toast = ToastMessage()

    while True:
        title = input("Title of notification: ")
        msg = input("Message of notification: ")
        toast.send_toast(title, msg)
        print("\n")
