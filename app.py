from flask import Flask
from flask import jsonify
from flask import request
from flask import render_template
from flask_sqlalchemy import SQLAlchemy

import requests
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

import os
from os.path import join, dirname

import sendemail

from datetime import datetime

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ['FLASK_SECRET_KEY']
db = SQLAlchemy(app)


import models

SCOPES = ' '.join(['https://www.googleapis.com/auth/gmail.readonly', 
          'https://www.googleapis.com/auth/contacts.readonly',
          'https://www.googleapis.com/auth/gmail.send']) 

CLIENT_SECRET_FILE = 'client_secret.json'
API_SERVICE_NAME = 'gmail'
API_VERSION = 'v2'

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
        sender_user = models.User.query.filter_by(email=sender_email).first()
        if sender_user is None:
            new_user = models.User(email=sender_email, name=sender_name)
            db.session.add(new_user)
            db.session.commit()
        elif sender_user.name is None:
            sender_user.name = sender_name
            db.session.commit()

        recipient_user = models.User.query.filter_by(email=recipient_email).first()
        if sender_user is None:
            new_user = models.User(email=recipient_email)
            db.session.add(new_user)
            db.session.commit()
        
        return send_initial_email(sender_name, sender_email, recipient_email)
    else:
        return render_template('hack_form.html')

@app.route('/authorize')
def authorize():
    # Check if client secrets file has been created
    if not os.path.isfile(os.path.relpath(CLIENT_SECRETS_FILE)):
        file = open(CLIENT_SECRETS_FILE, 'w')
        file.write(os.environ(CLIENT_SECRET))
        file.close()

    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)

    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    flask.session['state'] = state

    return flask.redirect(authorization_url)
    
@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

    return flask.redirect(flask.url_for('test_api_request'))

def send_initial_email(sender_name, sender_email, recipient_email):
    user = models.User.query.filter_by(email=sender_email).first()
    if user.token is None:
        return flask.redirect('authorize')
    sendemail.SendMessage(sender_name, sender_email, recipient_email, credentials);
    return render_template('hack_form.html')    



if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Specify a hostname and port that are set as a valid redirect URI
    # for your API project in the Google API Console.
    app.run()
