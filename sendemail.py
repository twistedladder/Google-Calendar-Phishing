import httplib2

import sys

import os
import oauth2client
from oauth2client import client, tools
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from apiclient import errors, discovery
import mimetypes
import string

SCOPES = ' '.join(['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/contacts.readonly',
          'https://www.googleapis.com/auth/gmail.send']) 

CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'phishing-201717'

def add_one_month(dt0):
    dt1 = dt0.replace(days=1)
    dt2 = dt1 + timedelta(days=32)
    dt3 = dt2.replace(days=1)
    return dt3

def get_credential_store():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'gmail-python-email-send.json')
    store = oauth2client.file.Storage(credential_path)
    return store

def get_credentials():
    store = get_credential_store()
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

#def SendMessage(sender, to, subject, msgHtml, msgPlain, attachmentFile=None):
def SendMessage(sender_name, sender_email, recipient_email):
    #get OAuth credentials
    credentials = get_credentials()

    #use OAuth access credentials to authorize API
    http = credentials.authorize(httplib2.Http())

    #build components of message
    subject = Template('Invitation: Meeting @ $date 2:30pm - 3:30pm (CDT) ($sender_name)')
    new_date = add_one_month(datetime.today()).strftime('%a %b %d, %Y')
    subject = subject.safe_substitute(date=new_date, sender_name=sender_name) 
    
    #build html calendar invite
    html = Template(fopen('templates/email_template.html','r').read())
    html = html.safe_substitute(date=new_date, sender_name=sender_name, sender_email=sender_email, recipient_email=recipient_email);


    service = discovery.build('gmail', 'v1', http=http)
    message = CreateMessageHtml(sender_email, recipient_email, subject, msgHtml, "")
    result = SendMessageInternal(service, "me", message)
    return result

def SendMessageInternal(service, user_id, message):
    try:
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        print('Message Id: %s' % message['id'])
        return message
    except errors.HttpError as error:
        print('An error occurred: %s' % error)
        return "Error"
    return "OK"

def CreateMessageHtml(sender, to, subject, msgHtml, msgPlain):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to
    msg.attach(MIMEText(msgPlain, 'plain'))
    msg.attach(MIMEText(msgHtml, 'html'))
    return {'raw': base64.urlsafe_b64encode(msg.as_string())}

