# Google-Calendar-Phishing
This is our Ethical Hacking (C S 378) final project.
It is for EDUCATIONAL PURPOSES ONLY.
This project was meant to demonstrate proof of concept of a phishing attack.
It should not be used as an actual phishing attack.


# Setup
These setup instructions assume that you have Python 2.7, pip, and postgresql installed.
Please install these requirements before beginning installation.
This setup also assumes you have already created a local postgresql (likely through psql or Postgres.app)

The following environment variables need to be set up:

APP_SETTINGS: This should be 'config.DevelopmentConfig' in development

CLIENT_SECRET: This is the Google OAuth Client Secret JSON (the entire string)

FLASK_SECRET_KEY: This can be any secret key you choose. Flask just uses it to maintain sessions

DATABASE_URL: This is the complete url to the database, which must be a postgresql database. For development, you'll likely be connecting to a local database with the format 'postgresql://[user]:[password]@localhost:5432/[database_name]'

REDIRECT_URL: This is the url that the OAuth protocol should redirect to after it authenticates with Google. For development, this should probably be http://localhost:5000/calendar.

GMAIL_USER: This is a gmail username, needed to connect to the gmail SMTP server to send the initial email.

GMAIL_PASSWORD: This is the gmail password for the gmail username.


To install Python dependencies, run the following command:
```
pip install -r requirements.txt
```

To run migrations for the database, run the following command:
```
python manage.py db upgrade
```

To run the app locally, run the following command:
```
python server.py
```

You can access the webapp at http://localhost:5000
