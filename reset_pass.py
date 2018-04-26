import google_api
import os
import oauth2client
from oauth2client import client, tools
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
import base64
import webbrowser
import requests
import database
from propagate import decode_message

# /api/password
# name
# email

def create_headers_dict(message):
    # transform headers into dict rather than list to make it easier to work with
    headers_dict = {}
    for header in message['payload']['headers']:
        headers_dict[header['name']] = header['value']

    return headers_dict

def find_reset_links(emails):
    """Returns all reset password links in a users email."""
    links = []
    for email in emails:
        msg = decode_message(email)
        # oh god
        if 'reset' in msg and 'password' in msg:
            msg = msg.split()
            # look for links
            for s in msg:
                if 'http' in s:
                    links.append(s)

    return links

def request_resets(email):
    """Requests a reddit password reset if email and username are the same."""
    uname = email.split('@')[0]
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    r = requests.post("https://www.reddit.com/api/password", data={'name': uname, 'email': email}, headers=headers)
    print r.content

def open_reset_links(service, email):
    links = []
    while True:
        print 'opening reset links attempt...'
        messages = google_api.get_messages(service) 
        links = find_reset_links(messages)
        if len(links) > 0:
            break
        # this is probably dumb
        sleep(20)

    print links
    for link in links:
        webbrowser.open(link)

if __name__ == '__main__':
    home_dir = os.path.expanduser('~')
    credential_path = os.path.join(home_dir, '.credentials', 'credential-calendarphishingtest123.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    http = credentials.authorize(httplib2.Http())

    gmail_service = discovery.build('gmail', 'v1', http=http)

    open_reset_links(gmail_service, 'contactthree003@gmail.com')
