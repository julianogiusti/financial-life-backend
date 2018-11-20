# -*- coding: utf-8 -*-
import base64
from datetime import datetime, timedelta
from hashlib import md5
import json
import os
from time import time
from flask import current_app, url_for
from flask_login import UserMixin
from sqlalchemy import null
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import rq
from app import db, login

# transaction types
INCOME = 1
EXPENSE = 2

class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data

class User(UserMixin, PaginatedAPIMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'last_seen': self.last_seen.isoformat() + 'Z',
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'avatar': self.avatar(128)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Account(PaginatedAPIMixin, db.Model):
    __tablename__ = 'account'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    account_type = db.Column(db.Integer, db.ForeignKey('account_type.id'))
    balance = db.Column(db.Numeric(12, 2), default=0.0)
    sum_on_dash = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'account_type': self.account_type,
            'balance': self.balance,
            'sum_on_dash': self.sum_on_dash
        }
        return data

    def from_dict(self, data, user_id=None):
        for field in ['id', 'name', 'account_type', 'balance', 'sum_on_dash']:
            if field in data:
                setattr(self, field, data[field])
        if user_id:
            setattr(self, 'user_id', user_id)


class AccountType(db.Model):
    __tablename__ = 'account_type'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(20), index=True)
    # account_type em account, mudar para:
    # 1 - conta_corrente
    # 2 - poupanca
    # 3 - dinheiro
    # 4 - corretora
    # 5 - investimentos
    # 6 - outra


class Transfer(PaginatedAPIMixin, db.Model):
    __tablename__ = 'transfer'
    id = db.Column(db.Integer, primary_key=True)
    from_account = db.Column(db.Integer, db.ForeignKey('account.id'))
    to_account = db.Column(db.Integer, db.ForeignKey('account.id'))
    amount = db.Column(db.Numeric(12,2))
    observation = db.Column(db.String(150))
    transfer_date = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        data = {
            'id': self.id,
            'from_account': self.from_account,
            'to_account': self.to_account,
            'amount': self.amount,
            'observation': self.observation,
            'transfer_date': self.transfer_date.isoformat() + 'Z',
        }
        return data

    def from_dict(self, data):
        for field in ['id', 'from_account', 'to_account', 'amount', 'observation', 'transfer_date']:
            if field in data:
                setattr(self, field, data[field])


class Transaction(PaginatedAPIMixin, db.Model):
    __tablename__ = 'transaction'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('account.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('transaction_category.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    value = db.Column(db.Numeric(12,2))
    description = db.Column(db.String(50))
    observation = db.Column(db.String(200))
    paid = db.Column(db.Boolean, default=False)
    transaction_type = db.Column(db.Integer)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        data = {
            'id': self.id,
            'account_id': self.account_id,
            'category_id': self.category_id,
            'value': self.value,
            'description': self.description,
            'observation': self.observation,
            'paid': self.paid,
            'transaction_type': self.transaction_type,
            'date_created': self.date_created.isoformat() + 'Z'
        }
        return data

    def from_dict(self, data, user_id=None):
        for field in ['id', 'account_id', 'category_id', 'value', 'description', 'observation', 'paid', 'transaction_type', 'date_created']:
            if field in data:
                setattr(self, field, data[field])
        if user_id:
            setattr(self, 'user_id', user_id)

class TransactionCategory(db.Model):
    __tablename__ = 'transaction_category'
    id = db.Column(db.Integer, primary_key=True)
    transaction_type = db.Column(db.Integer)
    description = db.Column(db.String(50))


class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    description = db.Column(db.String(50), index=True)


class TransactionTag(db.Model):
    __tablename__ = 'transaction_tag'
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'))
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'))