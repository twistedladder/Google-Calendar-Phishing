from flask import Flask
from flask import jsonify
from flask import request
from flask import render_template
import os
from os.path import join, dirname
import requests
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import sendemail
from datetime import datetime
app = Flask(__name__)

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
        sender_email = request.form.get('sender_email')
        sender_name = request.form.get('sender_name')
        recipient_email = request.form.get('recipient_email')
        
        return send_initial_email(sender_name, sender_email, recipient_email)
    else:
        return render_template('hack_form.html')
    

def send_initial_email(sender_name, sender_email, recipient_email):
    sendemail.SendMessage(sender_name, sender_email, recipient_email);
    return render_template('hack_form.html')    



if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Specify a hostname and port that are set as a valid redirect URI
    # for your API project in the Google API Console.
    app.run('localhost', 8080, debug=True)
