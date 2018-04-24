import database
import googleapiclient.discovery
import googleapiclient.errors

MESSAGE_LIMIT = 10
MAX_PAGE_SIZE = 2000

#use credentials to determine who the current user is
def get_user_info(credentials):
    people = googleapiclient.discovery.build(
      'people', 'v1', credentials=credentials)
    user_profile = people.people().get(resourceName='people/me', personFields='names,emailAddresses').execute()
    info = {'name': user_profile['names'][0]['displayName'],
            'email': user_profile['emailAddresses'][0]['value']}
    database.update_user(email=info['email'], name=info['name'])
    return info

#send email using google API
def send_email(service, message):
    try:
        message_response = service.users().messages().send(userId='me', body=message).execute()
        return [True, message_response['id']]
    except googleapiclient.errors.HttpError, error:
        return [False, error]

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

# Returns list of messages for authorized user
def get_messages(service):
    response = service.users().messages().list(userId='me', maxResults=MESSAGE_LIMIT).execute()
    msg_ids = [d['id'] for d in response['messages']]

    messages = []
    for msg_id in msg_ids:
        message = service.users().messages().get(userId='me', id=msg_id).execute()
        messages.append(message)
    return messages