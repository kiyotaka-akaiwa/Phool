#!/usr/bin/env python3

from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

username = input("Please enter the Gmail address you will be sending the email from: ")
password = input("Please enter the password for the account (Must be App Passwords): ")
target = input("Please enter the target's email address: ")

msg = MIMEMultipart('alternative')
msg['From'] = username
msg['To'] = target

template = input("Please enter the template you will be using: ")

if template == "Google Alert":
    msg['Subject'] = "Security alert"

    with open('templates/google-alert.html', 'r') as f:
        html = f.read()

    html.replace("EMAIL", target)

elif template == "Amazon Cancellation":
    msg['Subject'] = 'Your Amazon.com order of "2021 Apple MacBook P..." has been canceled.'

    with open('templates/amazon-cancellation.html', 'r') as f:
        html = f.read()

    firstname = input("Please enter the target's first name: ")

    html.replace("FIRSTNAME", firstname)
    html.replace("DATE", datetime.today().strftime("%A, %B %d, %Y"))

msg.attach(MIMEText(html, 'html'))

server = smtplib.SMTP('smtp.gmail.com', 587)
server.ehlo()
server.starttls()
server.login(username, password)
server.sendmail(username, target, msg.as_string())
server.quit()