from datetime import datetime
from sqlalchemy import exc, text, or_, and_

from app import database, config as config_module, ClassProperty

config = config_module.get_config()
db = database.AppRepository.db


class AbstractModel(object):
    class NotExist(Exception):
        pass

    class RepositoryError(Exception):
        pass

    @classmethod
    def create_from_json(cls, json_data):
        try:
            instance = cls()
            instance.set_values(json_data)
            instance.save_db()
            return instance
        except exc.IntegrityError as ex:
            raise cls.RepositoryError(ex.message)

    @classmethod
    def list_with_filter(cls, **kwargs):
        return cls.query.filter_by(**kwargs).all()

    @classmethod
    def list_all(cls):
        return cls.query.all()

    @classmethod
    def get_with_filter(cls, **kwargs):
        return cls.query.filter_by(**kwargs).one_or_none()

    @classmethod
    def get(cls, item_id):
        item = cls.query.get(item_id)
        if not item:
            raise cls.NotExist
        else:
            return item

    @classmethod
    def rollback_db(cls):
        db.session.rollback()

    def save_db(self):
        db.session.add(self)
        db.session.flush()
        db.session.refresh(self)

    def delete_db(self):
        try:
            db.session.delete(self)
            db.session.flush()
        except exc.IntegrityError as ex:
            raise self.RepositoryError(ex.message)

    def update_from_json(self, json_data):
        try:
            self.set_values(json_data)
            self.save_db()
            return self
        except exc.IntegrityError as ex:
            raise self.RepositoryError(ex.message)

    def set_values(self, json_data):
        for key, value in json_data.items():
            setattr(self, key, json_data.get(key, getattr(self, key)))


class User(db.Model, AbstractModel):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String)

    @classmethod
    def get_by_email(cls, email):
        return cls.get_with_filter(email=email)


class Account(db.Model):
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

class Transfer(db.Model):
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


class Transaction(db.Model):
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