#!/usr/bin/env python3

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

username = "my@gmail.com"
password = "password"
target = "target@gmail.com"

msg = MIMEMultipart('alternative')
msg['Subject'] = "Security alert"
msg['From'] = username
msg['To'] = target

with open('templates/google-alert.html', 'r') as f:
    html = f.read()

msg.attach(MIMEText(html, 'html'))

server = smtplib.SMTP('smtp.gmail.com', 587)
server.ehlo()
server.starttls()
server.login(username, password)
server.sendmail(username, target, msg.as_string())
server.quit()