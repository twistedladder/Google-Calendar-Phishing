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
import datetime

MAX_PAGE_SIZE = 2000
FREQUENT_CONTACT_COUNT = 2

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

    for email in sorted(send_counts, key=d.get, reverse=True)[:FREQUENT_CONTACT_COUNT]:
        if email in contact_info:
            contact_info[email]['frequent'] = True

    return contact_info

def send_emails_to_contacts(service, contacts, frequent=False, recent=False):
    contact_info = create_contact_dict(service, contacts)
    for contact in contact_info:
        if (frequent and contact['frequent']) and (recent and contact['recent']):
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

def propagate(credential_path):
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    http = credentials.authorize(httplib2.Http())

    gmail_service = discovery.build('gmail', 'v1', http=http)
    people_service = discovery.build('people', 'v1', http=http)

    contacts = get_contacts(people_service)
    save_contacts(gmail_service, contacts)
    send_emails_to_contacts(gmail_service, contacts)

    
if __name__ == '__main__':
    home_dir = os.path.expanduser('~')
    credential_path = os.path.join(home_dir, '.credentials', 'cred.json')
    print credential_path
    propagate(credential_path)
