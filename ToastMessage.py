import time
from plyer import notification


class ToastMessage:
    def send_toast(self, title, message, duration=600):
        notification.notify(title=title, message=message, timeout=duration)


if __name__ == "__main__":
    toast = ToastMessage()

    # while True:
    title = input("Title of notification: ")
    msg = input("Message of notification: ")
    toast.send_toast(title, msg, "assistant", 600)
    print("\n")
