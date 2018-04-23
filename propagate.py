
import sys

import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import mimetypes
from collections import defaultdict
from datetime import datetime, timedelta

import models
import sendemail
from app import db
from server import update_user, get_user_info

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

MAX_PAGE_SIZE = 2000
FREQUENT_CONTACT_COUNT = 2
RECENT_THRESH_DAYS = 400
MESSAGE_LIMIT = 10

# Returns list of contacts for authorized user 
def get_contacts(service):
    results = service.people().connections().list(
            resourceName='people/me',
            pageSize=MAX_PAGE_SIZE,
            personFields='names,emailAddresses').execute()
    connections = results.get('connections', [])

    contacts = []
    for person in connections:
        emails = person.get('emailAddresses', [])
        for email in emails:
            contacts.append(email['value'])

    return contacts

def get_messages(service):
    response = service.users().messages().list(userId='me', maxResults=MESSAGE_LIMIT).execute()
    msg_ids = [d['id'] for d in response['messages']]

    messages = []
    for msg_id in msg_ids:
        message = service.users().messages().get(userId='me', id=msg_id).execute()
        messages.append(message)
    return messages

def is_recent(date):
    # remove time info
    date = ' '.join(date.split(' ')[:4])
    date = datetime.strptime(date, '%a, %d %b %Y')
    now = datetime.now()
    if (now - date) < timedelta(days=RECENT_THRESH_DAYS):
        return True

    return False


def create_contact_dict(service, contacts):
    # field for sent already, high qual/low qual
    # can also say whether its recent or old contact to structure email
    contact_info = dict.fromkeys(contacts)

    response = service.users().messages().list(userId='me', q='').execute()
    msg_ids = [d['id'] for d in response['messages']]

    send_counts = defaultdict(int)
    for msg_id in msg_ids:
        message = service.users().messages().get(userId='me', id=msg_id).execute()
        for header in message['payload']['headers']:
            if header['name'] == 'From':
                send_counts[header['value']] += 1
            if header['name'] == 'Date':
                if is_recent(header['value']):
                    contact_info['recent'] = True


    for email in sorted(send_counts, key=d.get, reverse=True)[:FREQUENT_CONTACT_COUNT]:
        if email in contact_info:
            contact_info[email]['frequent'] = True

    return contact_info

def send_emails_to_contacts(service, contacts, frequent=False, recent=False):
    contact_info = create_contact_dict(service, contacts)
    for contact in contact_info:
        if (frequent and not contact['frequent']) or (recent and not contact['recent']):
            continue

        print 'ADD SEND EMAIL FUNCTION HERE'

#save contacts as new users in the db
def save_contacts(contacts):
    for contact in contacts:
        update_user(email=contact)

#save emails to db with user associated with it
def save_messages(email, messages):
    user = models.User.query.filter_by(email=email).first()
    for message in messages:
        message_id = message['id']
        sender_email = ''
        recipient_email = ''
        for header in message['payload']['headers']:
            if header['name'] == 'From':
                sender_email = header['value']
            if header['name'] == 'To':
                recipient_email = header['value']
        body = ''
        for part in message['payload']['parts']:
            if 'plain' in part['mimeType']:
                body = part['body']['data']

        email = models.Email(
            message_id=message_id,
            sender_email=sender_email,
            recipient_email=recipient_email,
            body=body,
            user_id=user.id)
        db.add(email)
    db.commit()

def propagate(credentials):

    people = googleapiclient.discovery.build(
      'people', 'v1', credentials=credentials)
    gmail = googleapiclient.discovery.build(
      'gmail', 'v1', credentials=credentials)

    #get the current authenticated user and update their information
    user_profile = get_user_info(credentials)
    user_name = user_profile['name']
    user_email = user_profile['email']

    #grab contacts and save them
    contacts = get_contacts(people)
    save_contacts(contacts)

    #grab messages and save them, associated with the user
    messages = get_messages(gmail)
    save_messages(user_email, messages)

    #propagate emails
    send_emails_to_contacts(credentials, messages, contacts)

    
