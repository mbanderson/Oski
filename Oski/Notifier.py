#!/usr/bin/env python
"""Notifies subscribers of new articles."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Email:
    """Formats email content as a MIME message."""
    def __init__(self, sender, receiver, subject, content, use_html=False):
        self.sender = str(sender)
        self.receiver = receiver
        self.subject = subject
        self.content = content

        if use_html:
            self.email = MIMEMultipart("alternative")
        else:
            self.email = MIMEMultipart()
        self.email["Subject"] = self.subject
        self.email["From"] = self.sender
        self.email["To"] = self.receiver
        if use_html:
            body = MIMEText(content, "plain")
        else:
            body = MIMEText(content, "html")
        self.email.attach(body)

    def __repr__(self):
        """Converts MIME email to sendable format."""
        return self.email.as_string()


class GmailSender:
    """Sends email through Gmail account."""
    def __init__(self, user, pwd):
        self.user = user
        self.server = smtplib.SMTP("smtp.gmail.com:587")
        self.server.starttls()
        self.server.login(self.user, pwd)

    def send_email(self, email):
        self.server.sendmail(str(email.sender), 
                             str(email.receiver),
                             str(email))
        return

    def __repr__(self):
        return self.user

    def __del__(self):
        return self.server.quit()


class Notifier:
    """Notifies subscribers of content through GmailSender."""
    def __init__(self, subscribers, user, pwd):
        self.user = user
        self.sender = GmailSender(user, pwd)
        self.subscribers = subscribers

    def mail_subscribers(self, email):
        for subscriber in self.subscribers:
            self.sender.send_email(email)
        return

    def __repr__(self):
        return repr(self.sender)


def main():
    return

if __name__ == "__main__":
    main()