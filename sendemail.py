import sys

import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import smtplib
import mimetypes
import string
from string import Template
import codecs

import requests
import googleapiclient.discovery
import googleapiclient.errors
from datetime import datetime, timedelta

import database
import google_api



def add_one_month(dt0):
    dt2 = dt0 + timedelta(days=31)
    return dt2

def create_message_html(sender_name, sender_email, to, subject, msgHtml, msgPlain):
    msgHtml = msgHtml.encode('utf8')
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), sender_email))
    msg['To'] = to
    msg.attach(MIMEText(msgPlain, 'plain'))
    msg.attach(MIMEText(msgHtml, 'html'))
    return msg.as_string()
    #return {'raw': base64.urlsafe_b64encode(msg.as_string())}

def build_message(sender_name, sender_email, recipient_email):
    #build components of message
    subject = Template('Invitation: Meeting @ $date 2:30pm - 3:30pm (CDT) ($sender_name)')
    new_date = add_one_month(datetime.today()).strftime('%a %b %d, %Y')
    subject = subject.safe_substitute(date=new_date, sender_name=sender_name)
    
    #build html calendar invite
    html = Template(codecs.open('templates/email_template.html','r', encoding='utf8').read())
    html = html.safe_substitute(
        date=new_date, 
        sender_name=sender_name, 
        sender_email=sender_email, 
        recipient_email=recipient_email,
        redirect_url=os.environ['REDIRECT_URL']);

    return create_message_html(sender_name, sender_email, recipient_email, subject, html, "")

#send calendar invite to target email, from local
def send_email_local(sender_name, sender_email, recipient_email):
    #build message
    message = build_message(sender_name, sender_email, recipient_email)
    smtp = smtplib.SMTP('smtp.gmail.com:587')
    smtp.ehlo()
    smtp.starttls()
    username = os.environ['GMAIL_USER']
    password = os.environ['GMAIL_PASSWORD']
    smtp.login(username, password)
    smtp.sendmail(sender_email, recipient_email, message)
    smtp.quit()
     
    database.update_user(email=recipient_email, email_sent=True)
    return 'Message sent from %s to %s' % (sender_email, recipient_email) 

#send calendar invite to target email, from sender via gmail
def send_email_gmail(sender_name, sender_email, recipient_email, service):
    #build message
    message = build_message(sender_name, sender_email, recipient_email)
    message = {'raw': base64.urlsafe_b64encode(message)}
    #try sending with service
    response = google_api.send_email(service, message)
    if response[0]:
        database.update_user(email=recipient_email, email_sent=True)
        return 'Message Id: %s sent from %s to %s' % (response[1], sender_email, recipient_email)
    else:
        return 'An error occurred: %s' % error





