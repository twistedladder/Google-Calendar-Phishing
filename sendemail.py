import sys

import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
import string
from string import Template
import codecs

import requests
import googleapiclient.discovery
import googleapiclient.errors
from datetime import datetime, timedelta

API_SERVICE_NAME = 'gmail'
API_VERSION = 'v1'

def add_one_month(dt0):
    dt1 = dt0.replace(day=1)
    dt2 = dt1 + timedelta(days=32)
    dt3 = dt2.replace(day=1)
    return dt3

def create_message_html(sender, to, subject, msgHtml, msgPlain):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to
    msg.attach(MIMEText(msgPlain, 'plain'))
    msg.attach(MIMEText(msgHtml, 'html'))
    return {'raw': base64.urlsafe_b64encode(msg.as_string())}

def build_message(sender_name, sender_email, recipient_email):
    #build components of message
    subject = Template('Invitation: Meeting @ $date 2:30pm - 3:30pm (CDT) ($sender_name)')
    new_date = add_one_month(datetime.today()).strftime('%a %b %d, %Y')
    subject = subject.safe_substitute(date=new_date, sender_name=sender_name) 
    
    #build html calendar invite
    html = Template(codecs.open('templates/email_template.html','r', encoding='utf8').read())
    html = html.safe_substitute(date=new_date, sender_name=sender_name, sender_email=sender_email, recipient_email=recipient_email);

    return create_message_html(sender_email, recipient_email, subject, html, "")

#def SendMessage(sender, to, subject, msgHtml, msgPlain, attachmentFile=None):
def send_email(sender_name, sender_email, recipient_email, credentials):
    #build message
    message = build_message(sender_name, sender_email, recipient_email)
    #try sending with service
    gmail = googleapiclient.discovery.build(
      API_SERVICE_NAME, API_VERSION, credentials=credentials)

    try:
        message_response = gmail.users().messages().send(userId='me', body=message).execute()
        return 'Message Id: %s sent from %s to %s' % (message['id'], sender_email, recipient_email)
    except googleapiclient.errors.HttpError, error:
        return 'An error occurred: %s' % error





