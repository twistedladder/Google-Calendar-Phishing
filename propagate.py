
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

# gets just the email from a weird header string
def remove_name_from_contact(email):
    email = email.split()
    # format is weird in this case
    if len(email) > 1:
        # rm name
        email = email[-1]
        # rm tags
        email = email[1:-1]

    email = ''.join(email)
    return email

def create_contact_dict(messages, contacts):
    # field for sent already, high qual/low qual
    # can also say whether its recent or old contact to structure email
    contact_info = dict.fromkeys(contacts)


    send_counts = defaultdict(int)
    recent_contacts = set()
    for message in messages:
        email = None
        # transform headers into dict rather than list to make it easier to work with
        headers_dict = {}
        for header in message['payload']['headers']:
            headers_dict[header['name']] = header['value']

        from_mail = remove_name_from_contact(headers_dict['From'])
        to_mail = remove_name_from_contact(headers_dict['To'])

        send_counts[from_mail] += 1
        send_counts[to_mail] += 1
        if is_recent(headers_dict['Date']):
            recent_contacts.add(from_mail)
            recent_contacts.add(to_mail)

    frequent_contacts = set()
    for email in sorted(send_counts, key=d.get, reverse=True):
        if len(frequent_contacts) > FREQUENT_CONTACT_COUNT:
            break

        # only care about frequent people in your contacts, not over all messages
        if email in contacts:
            frequent_contacts.add(email)

    for contact in contact_info:
        contact_info[contact] = {}
        if contact in frequent_contacts:
            contact_info[contact]['frequent'] = True

        if contact in recent_contacts:
            contact_info[contact]['recent'] = True

    return contact_info

def send_emails_to_contacts(credentials, messages, contacts, sender_email, sender_name, frequent=False, recent=False):
    contact_info = create_contact_dict(message, contacts)
    for contact in contact_info:
        user = models.User.query.filter_by(email=contact).first()
        if  (frequent and not contact['frequent']) or 
            (recent and not contact['recent']) or
            (user.email_sent):
            continue

        print('sending email from %s to %s' % (sender_email, contact)
)
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
                sender_email = remove_name_from_contact(header['value'])
            if header['name'] == 'To':
                recipient_email = remove_name_from_contact(header['value'])
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
    send_emails_to_contacts(credentials, messages, contacts, user_email, user_name)

    
