import time
# import wallpaper
from image_crawler import ImageCrawler
from send_email import EmailMessage, EmailService
from send_toast import ToastMessage


def main():
    while True:
        print("\n*** Choose from the following utilities ***")
        print("[1] Image Scraper")
        print("[2] Change Wallpaper")
        print("[3] Send Email")
        print("[4] Create Notification")
        response = input("What do you choose?: ").strip()

        if response == "1":
            scraper = ImageCrawler()
            scraper.start()
            continue
        elif response == "2":

            pass
        elif response == "3":
            email = EmailMessage()
            mail_service = EmailService()
            # TODO: create a loop option menu for email
            continue
        elif response == "4":
            toast = ToastMessage()
            title = input("Title of notification: ")
            msg = input("Message of notification: ")
            toast.send_toast(title, msg)
            print("\n")
            continue


if __name__ == "__main__":
    main()
