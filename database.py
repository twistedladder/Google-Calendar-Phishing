from app import db
import models


def query_user(id=None, email=None):
    if id is not None:
        return models.User.query.filter_by(id=id).first()
    elif email is not None:
        return models.User.query.filter_by(email=email).first()
    else:
        return None

def query_email(id=None, user_id=None):
    if id is not None:
        return models.Email.query.filter_by(id=id).first()
    elif user_id is not None:
        return models.Email.query.filter_by(user_id=user_id).all()
    else:
        return None

def query_all_users():
    return models.User.query.all()

#updates the user based on parameters, or creates if user does not exist
def update_user(email, name=None, credentials=None, email_sent=False):
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
    if email_sent:
        user.email_sent = True
    #print (models.object_as_dict(user))
    db.session.add(user)
    db.session.commit()
    return user

#updates the email based on parameters, or creates if email does not exist
def update_email(message_id, sender_email, recipient_email, body, user_id):
    email = models.Email.query.filter_by(message_id=message_id).first()
    #print (models.object_as_dict(user))
    if email is None:
        print('creating new email')
        email = models.Email()
        email.message_id = message_id

    email.sender_email = sender_email
    email.recipient_email = recipient_email
    email.body = body
    email.user_id = user_id
    db.session.add(email)
    db.session.commit()
    return email