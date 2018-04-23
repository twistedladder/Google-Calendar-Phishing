from app import *
import models

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/contacts.readonly',
          'https://www.googleapis.com/auth/gmail.send']

CLIENT_SECRET_FILE = 'client_secret.json'
API_SERVICE_NAME = 'gmail'
API_VERSION = 'v1'

@app.route('/')
def homepage():
    the_time = datetime.now().strftime("%A, %d %b %Y %l:%M %p")

    return """
    <h1>Hello heroku</h1>
    <p>It is currently {time}.</p>
    <img src="http://loremflickr.com/600/400" />
    """.format(time=the_time)

@app.route('/hack', methods=['GET', 'POST'])
def hack_form():
    if request.method == 'POST':
        #extract post parameters
        sender_email = request.form.get('sender_email')
        sender_name = request.form.get('sender_name')
        recipient_email = request.form.get('recipient_email')

        #add sender and recipient to db if they don't exist
        update_user(email=sender_email, name=sender_name)
        #update_user(email=recipient_email)
        
        return send_initial_email(sender_name, sender_email, recipient_email)
    else:
        return render_template('hack_form.html')

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
    sender_name = request.args.get('sender_name')
    sender_email = request.args.get('sender_email')
    recipient_email = request.args.get('recipient_email')
    return send_initial_email(sender_name, sender_email, recipient_email)



### HELPER FUNCTIONS ###

#updates the user based on parameters, or creates if user does not exist
def update_user(email, name=None, credentials=None):
    user = models.User.query.filter_by(email=email).first()
    #print (models.object_as_dict(user))
    if user is None:
        print('creating new user')
        user = models.User()
        user.email = email

    if name is not None:
        user.name = name
    if credentials is not None:
        user.token = credentials['token']
        user.refresh_token = credentials['refresh_token']
        user.token_uri = credentials['token_uri']
        user.client_id = credentials['client_id']
        user.client_secret = credentials['client_secret']
        user.scopes = ' '.join(credentials['scopes'])
    #print (models.object_as_dict(user))
    db.session.add(user)
    db.session.commit()
    #return user


def send_initial_email(sender_name, sender_email, recipient_email):
    print(sender_name, sender_email, recipient_email)
    user = models.User.query.filter_by(email=sender_email).first()
    if user.token is None:
        #db.session.flush()
        flask.session['sender_name'] = sender_name
        flask.session['sender_email'] = sender_email
        flask.session['recipient_email'] = recipient_email

        return flask.redirect(flask.url_for('authorize_initial'))
    else:
        credentials = google.oauth2.credentials.Credentials(**user_to_credentials(user))
        #db.session.flush()
        return sendemail.send_email(sender_name, sender_email, recipient_email, credentials);
        


#check if client secret file is present, create if it's not
def check_client_secret():
    if not os.path.isfile(os.path.relpath(CLIENT_SECRET_FILE)):
        file = open(CLIENT_SECRET_FILE, 'w')
        file.write(os.environ['CLIENT_SECRET'])
        file.close()

#use credentials to determine who the current user is
def get_email_address(credentials):
    gmail = googleapiclient.discovery.build(
      API_SERVICE_NAME, API_VERSION, credentials=credentials)
    userProfile = gmail.users().getProfile(userId='me').execute()
    return userProfile['emailAddress']

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
    user_email = get_email_address(credentials)
    print ('email is ', user_email)
    credentials_dict = credentials_to_dict(credentials)
    update_user(email=user_email, credentials=credentials_dict)


def authorize(redirect_url):
    check_client_secret()

    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE, scopes=SCOPES)

    flow.redirect_uri = flask.url_for(redirect_url, _external=True,)

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
    check_client_secret()
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for(redirect_url, _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials

    store_credentials(credentials)

    return flask.redirect(flask.url_for(success_url))


if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Specify a hostname and port that are set as a valid redirect URI
    # for your API project in the Google API Console.
    app.run()