# Google-Calendar-Phishing
Ethical Hacking final project
EDUCATIONAL PURPOSES ONLY
This project was meant to demonstrate proof of concept of a phishing attack.
It should not be used as an actual phishing attack.


Setup:
The following environment variables need to be set up:
APP_SETTINGS: This should be 'config.DevelopmentConfig' in development
CLIENT_SECRET: This is the Google OAuth Client Secret JSON (the entire string)
FLASK_SECRET_KEY: This can be any secret key you choose. Flask just uses it to maintain sessions
DATABASE_URL: This is the complete url to the database, which must be a postgresql database. For development, you'll likely be connecting to a local database with the format 'postgresql://[user]:[password]@localhost:5432/[database_name]'


To run migrations for the database, run the following command:
```
python manage.py db upgrade
```

To run the app locally, run the following command:
```
python app.py
```
