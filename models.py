from app import db
from flask_sqlalchemy import SQLAlchemy
import datetime

class BaseModel(db.Model):
    """Base data model for all objects"""
    __abstract__ = True

    def __init__(self, *args):
        super().__init__(*args)

    def __repr__(self):
        """Define a base way to print models"""
        return '%s(%s)' % (self.__class__.__name__, {
            column: value
            for column, value in self._to_dict().items()
        })

    def json(self):
        """
                Define a base way to jsonify models, dealing with datetime objects
        """
        return {
            column: value if not isinstance(value, datetime.date) else value.strftime('%Y-%m-%d')
            for column, value in self._to_dict().items()
        }


class User(BaseModel, db.Model):
	__tablename__ = 'user'

	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(120), unique=True, nullable=False)
	name = db.Column(db.String(120), nullable=True)
	token = db.Column(db.Text, nullable=True)
	refresh_token = db.Column(db.Text, nullable=True)
	token_uri = db.Column(db.Text, nullable=True)
	client_id = db.Column(db.Text, nullable=True)
	client_secret = db.Column(db.Text, nullable=True)
	scopes = db.Column(db.Text, nullable=True)
	emails = db.relationship('Email', backref='user', lazy=True)


class Email(BaseModel, db.Model):
	__tablename__ = 'email'

	id = db.Column(db.Integer, primary_key=True)
	message_id = db.Column(db.Text, nullable=False)
	sender_email = db.Column(db.String(120), nullable=False)
	body = db.Column(db.Text, nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)