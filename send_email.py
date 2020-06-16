"""
    this is a class utility for sending email using SMTP
    - able to send basic email (w/ subject, body and recipients)
    - able to attach basic files such as image type and octet type
"""

import os
import ntpath
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import imghdr


class HostSetting:
    def __init__(self):
        self.host_name = "smtp.gmail.com"
        self.port_number = 465
        self.host_email = os.environ.get("GOOGLE_EMAIL")
        self.password = os.environ.get("GOOGLE_EMAIL_PASSWORD")


class EmailMessage:
    def __init__(self):
        self.subject = "(NO SUBJECT)"
        self.recipient = []  # comma separated list of recipients
        self.body = ""
        self.attachment = []  # comma separated list of attachment file directories


class EmailService(HostSetting):
    def __init__(self):
        super().__init__()

    def send_email(self, email: EmailMessage):
        self.response = []
        msg = MIMEMultipart()
        msg["Subject"] = email.subject
        msg["From"] = self.host_email
        msg["To"] = ", ".join(email.recipient)
        message_body = email.body

        # internal method to classify types
        # e.g.: "image" and "jpeg", "application" and "octet-stream"

        def _attachment_type(file_type):
            main_type = None
            sub_type = None

            image_sub_types = ["tif", "tiff", "png", "pic", "pcd", "pbm",
                               "jpg", "jpeg", "jpe", "jfif", "pjpeg", "pjp", "gif", "bmp"]
            if file_type in image_sub_types:
                main_type = "image"
                sub_type = file_type
            else:
                main_type = "application"
                sub_type = "octet-stream"

            return main_type, sub_type

        # internal method to process a email attachment

        def _process_attachment():
            for att in email.attachment:
                with open(att, "rb") as f:
                    file_type = imghdr.what(f.name)
                    # e.g.: "image" and "jpeg", "application" and "octet-stream"
                    main_type, sub_type = _attachment_type(file_type)
                    # set classification of attachment (main type and sub-type)
                    attachment = MIMEBase(main_type, sub_type)

                    # set attachment payload from binary code file
                    attachment.set_payload(f.read())
                    # change the payload into encoded form
                    encoders.encode_base64(attachment)

                    # use ntpath to get base name of attachent dir
                    # remove spaces in-between filename, issues in attachment header
                    filename = ntpath.basename(
                        f.name).replace(" ", "-").strip()
                    # header for attachments
                    attachment.add_header(
                        "Content-Disposition", f"attachment; filename={filename}")

                    # attach each instance of 'attachment' to instance 'msg'
                    msg.attach(attachment)

        # attach the email_body with the msg instance
        msg.attach(MIMEText(message_body, "plain"))

        if email.attachment:
            _process_attachment()

        # setup smtp class to send the email using credentials
        with smtplib.SMTP_SSL(host=self.host_name, port=self.port_number) as smtp:
            smtp.login(self.host_email, self.password)
            # send email message and return something
            response = smtp.send_message(msg)

        return "Sent!"


"""

Sample implementation:
1. create instance of EmailMessage() to create contents of email
2. create instance of EmailService() that will send the email message object

email = EmailMessage()
mail_service = EmailService()

email.recipient = ["emial_1@gmail.com", "emial_2@gmail.com"]
email.subject = "< subject >"
email.body = "< body of email here >"

email.attachment = ["File 1.doc", "./Images/Image 2.jpg", "c:/User/Pictures/document 3.pdf"]
# send email
status = mail_service.send_email(email)
print(f"Status: {status}\n")

"""
