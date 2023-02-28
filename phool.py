#!/usr/bin/env python3

import os
import re
import socket
import configparser
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from PyInquirer import prompt, Validator, ValidationError
import openai

CONFIG_FILE = 'config.ini'

class EmailValidator(Validator):
    def validate(self, document):
        email = document.text
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValidationError(
                message='Please enter a valid email address',
                cursor_position=len(document.text)
            )

class UrlValidator(Validator):
    def validate(self, document):
        url = document.text
        if not re.match(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+", url):
            raise ValidationError(
                message='Please enter a valid URL',
                cursor_position=len(document.text)
            )

class SmtpValidator(Validator):
    def validate(self, document):
        smtp_server = document.text
        try:
            socket.gethostbyname(smtp_server)
        except socket.gaierror:
            raise ValidationError(
                message='Please enter a valid SMTP server address',
                cursor_position=len(document.text)
            )

class TcpPortValidator(Validator):
    def validate(self, document):
        tcp_port = document.text
        try:
            tcp_port = int(tcp_port)
            if tcp_port < 1 or tcp_port > 65535:
                raise ValueError()
        except ValueError:
            raise ValidationError(
                message='Please enter a valid TCP port number (1-65535)',
                cursor_position=len(document.text)
            )

def main():
    answer = prompt({
            'type': 'list',
            'name': 'module',
            'message': 'Welcome to Phishing Template. Please choose a module you would like to use:',
            'choices': ['Templates', 'ChatGPT']
    })
    msg = MIMEMultipart('alternative')
    if answer['module'] == 'Templates':
        sender_email, target_email, subject, html = ask_templates()
    elif answer['module'] == 'ChatGPT':
        sender_email, target_email, subject, html = ask_chatgpt()
    msg['From'] = sender_email
    msg['To'] = target_email
    msg['Subject'] = subject
    msg.attach(MIMEText(html, 'html'))
    server, port, username, password = ask_smtp()
    send_mail(server, port, username, password, sender_email, target_email, msg)
    print('Email sent.')

def ask_templates():
    answers = prompt([
        {
            'type': 'list',
            'name': 'template',
            'message': 'Please choose a template you would like to use: ',
            'choices': ['Google Security Alert', 'Amazon Cancellation']
        },
        {
            'type': 'input',
            'name': 'sender_email',
            'message': 'Please enter the sender\'s email address:',
            'validate': EmailValidator
        },
        {
            'type': 'input',
            'name': 'target_email',
            'message': 'Please enter the target\'s email address:',
            'validate': EmailValidator
        }
    ])
    if answers['template'] == 'Google Security Alert':
        subject = "Security alert"
        with open('templates/google-alert.html', 'r') as f:
            html = f.read()
        html = html.replace("EMAIL", answers['target_email'])
    if answers['template'] == 'Amazon Cancellation':
        answer = prompt({
            'type': 'input',
            'name': 'target_name',
            'message': 'Please enter the target\'s first name:'
        })
        subject = 'Your Amazon.com order of "2021 Apple MacBook P..." has been canceled.'
        with open('templates/amazon-cancellation.html', 'r') as f:
            html = f.read()
        html = html.replace("FIRSTNAME", answer['target_name'])
        html = html.replace("DATE", datetime.today().strftime("%A, %B %d, %Y"))
    return answers['sender_email'], answers['target_email'], subject, html

def ask_chatgpt():
    config = configparser.ConfigParser()

    if os.path.isfile(CONFIG_FILE):
        config.read(CONFIG_FILE)
        openai_org = config.get('Settings', 'OPENAI_ORG', fallback='')
        openai_api_key = config.get('Settings', 'OPENAI_API_KEY', fallback='')
    else:
        openai_org = ''
        openai_api_key = ''

    answers = prompt([
        {
            'type': 'input',
            'name': 'openai_org',
            'message': 'Please enter the OpenAI Organization ID:',
            'default': openai_org
        },
        {
            'type': 'input',
            'name': 'openai_api_key',
            'message': 'Please enter the OpenAI API Key:',
            'default': openai_api_key
        }
    ])

    if not config.has_section('Settings'):
        config.add_section('Settings')

    config.set('Settings', 'OPENAI_ORG', answers['openai_org'])
    config.set('Settings', 'OPENAI_API_KEY', answers['openai_api_key'])

    with open(CONFIG_FILE, 'w') as config_file:
        config.write(config_file)

    openai.organization = answers['openai_org']
    openai.api_key = answers['openai_api_key']
    model_id = 'text-davinci-003'

    answers = prompt([
        {
            'type': 'input',
            'name': 'situation',
            'message': 'Please enter the situation of the email:'
        },
        {
            'type': 'input',
            'name': 'website',
            'message': 'Please enter the website URL you would like the target to access:',
            'validate': UrlValidator
        },
        {
            'type': 'input',
            'name': 'sender_name',
            'message': 'Please enter the sender\'s name:'
        },
        {
            'type': 'input',
            'name': 'sender_email',
            'message': 'Please enter the sender\'s email address:',
            'validate': EmailValidator
        },
        {
            'type': 'input',
            'name': 'sender_detail',
            'message': 'Please enter the detail of the sender:'
        },
        {
            'type': 'input',
            'name': 'target_name',
            'message': 'Please enter the target\'s name:'
        },
        {
            'type': 'input',
            'name': 'target_email',
            'message': 'Please enter the target\'s email address:',
            'validate': EmailValidator
        },
        {
            'type': 'input',
            'name': 'target_detail',
            'message': 'Please enter the detail of the target:'
        }
    ])

    request = (f'''Situation: {answers['situation']}
Website URL: {answers['website']}
Sender: {answers['sender_name']} {answers['sender_email']}
About Sender: {answers['sender_detail']}
Recipient: {answers['target_name']} {answers['target_email']}
About Recipient: {answers['target_detail']}

Please create an email that has a high chance of the recipient clicking the URL.
Please respond me only with a subject and an email body formatted in HTML that can be sent directly without any modification.
Please utilize the information given to tailor the email accordingly.
Please make sure that the email doesn't look like a phishing email.''')

    confirm = False
    while confirm == False:
        completion = openai.Completion.create(engine=model_id, prompt=request, max_tokens=512)
        response = completion.choices[0].text.lstrip()

        subject, message = response.split('\n', 1)
        subject = re.findall(r'(?<=Subject: ).*', subject)

        print("Subject: ", subject)
        print("Message: ", message)

        answer = prompt({
            'type': 'confirm',
            'name': 'confirm',
            'message': 'Would you like to proceed with sending an email with the above content?',
            'default': True
        })

        confirm = answer['confirm']

    return answers['sender_email'], answers['target_email'], subject[0].lstrip(), message.lstrip()

def ask_smtp():
    config = configparser.ConfigParser()

    if os.path.isfile(CONFIG_FILE):
        config.read(CONFIG_FILE)
        server = config.get('Settings', 'SMTP_SERVER', fallback='')
        port = config.get('Settings', 'SMTP_PORT', fallback='')
        username = config.get('Settings', 'SMTP_USERNAME', fallback='')
        password = config.get('Settings', 'SMTP_PASSWORD', fallback='')
    else:
        openai_org = ''
        openai_api_key = ''

    answers = prompt([
        {
            'type': 'input',
            'name': 'server',
            'message': 'Please enter the SMTP server hostname:',
            'default': server,
            'validate': SmtpValidator
        },
        {
            'type': 'input',
            'name': 'port',
            'message': 'Please enter the SMTP server port:',
            'default': port,
            'validate': TcpPortValidator
        },
        {
            'type': 'input',
            'name': 'username',
            'message': 'Please enter your username:',
            'default': username
        },
        {
            'type': 'password',
            'name': 'password',
            'message': 'Please enter your password:',
            'default': password
        },


    ])

    if not config.has_section('Settings'):
        config.add_section('Settings')

    config.set('Settings', 'SMTP_SERVER', answers['server'])
    config.set('Settings', 'SMTP_PORT', answers['port'])
    config.set('Settings', 'SMTP_USERNAME', answers['username'])
    config.set('Settings', 'SMTP_PASSWORD', answers['password'])

    with open(CONFIG_FILE, 'w') as config_file:
        config.write(config_file)

    return answers['server'], answers['port'], answers['username'], answers['password']

def send_mail(server, port, username, password, sender_email, target_email, msg):
    server = smtplib.SMTP(server, port)
    server.ehlo()
    server.starttls()
    server.login(username, password)
    server.sendmail(sender_email, target_email, msg.as_string())
    server.quit()

if __name__ == "__main__":
    main()
