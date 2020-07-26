import time
from plyer import notification


class ToastMessage:

    def send_toast(self, title, message, app_name="Virtual Assistant", duration=600):
        notification.notify(title=title, message=message, app_icon="C:\\Users\\Dave\\DEVENV\\Python\\PythonUtilityProjects\\brenda.ico", timeout=duration)


if __name__ == "__main__":
    toast = ToastMessage()

    while True:
        title = input("Title of notification: ")
        msg = input("Message of notification: ")
        toast.send_toast(title, msg)
        print("\n")
