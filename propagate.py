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
from collections import defaultdict
from datetime import datetime, timedelta

import models
from app import db

MAX_PAGE_SIZE = 2000
FREQUENT_CONTACT_COUNT = 2
RECENT_THRESH_DAYS = 400

#get name
def get_contacts(service):
    """ Returns list of contacts for authorized user 
    (this should be replaced by code that gets the contacts for a specified user
    or all the users we have auth tokens for)
    """
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

def create_contact_dict(service, contacts):
    # field for sent already, high qual/low qual
    # can also say whether its recent or old contact to structure email
    contact_info = dict.fromkeys(contacts)

    response = service.users().messages().list(userId='me', q='').execute()
    msg_ids = [d['id'] for d in response['messages']]

    send_counts = defaultdict(int)
    recent_contacts = set()
    for msg_id in msg_ids:
        message = service.users().messages().get(userId='me', id=msg_id).execute()
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

def send_emails_to_contacts(service, contacts, frequent=False, recent=False):
    contact_info = create_contact_dict(service, contacts)
    for contact in contact_info:
        if (frequent and not contact['frequent']) or (recent and not contact['recent']):
            continue

        print 'ADD SEND EMAIL FUNCTION HERE'


def save_contacts(service, contacts):
    """ Appends contact list to 'emails' file in home dir """
    email_dir = os.path.join(os.path.expanduser('~'), 'emails')
    if not os.path.exists(email_dir):
        os.makedirs(email_dir)

    my_profile = service.users().getProfile(userId='me').execute()
    my_id = my_profile['emailAddress'].split('@')[0]
    email_file = os.path.join(email_dir, my_id)
    print email_file
    with open(email_file, 'a') as f:
        for contact in contacts:
            f.write(contact)
            f.write('\n')

def propagate(credentials):
    http = credentials.authorize(httplib2.Http())

    gmail_service = discovery.build('gmail', 'v1', http=http)
    people_service = discovery.build('people', 'v1', http=http)

    contacts = get_contacts(people_service)
    save_contacts(gmail_service, contacts)
    send_emails_to_contacts(gmail_service, contacts)

    
if __name__ == '__main__':
    home_dir = os.path.expanduser('~')
    credential_path = os.path.join(home_dir, '.credentials', 'gmail-python-email-send.json')
    print credential_path
    propagate(credential_path)
