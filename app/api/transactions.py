# -*- coding: utf-8 -*-
from flask import jsonify, request, url_for
from app import db
from app.api.errors import bad_request
from app.models import User, Account, Transaction, TransactionCategory, TransactionTag, INCOME, EXPENSE
from app.api import bp
from app.api.auth import token_auth

@bp.route('/users/<int:user_id>/incomes', methods=['POST'])
def create_income(user_id):
    data = request.get_json() or {}

    if 'paid' in data and data['paid']:
        acc_to_update = Account.query.filter_by(id=data['account_id']).first()
        print(acc_to_update.balance)
        acc_to_update.balance = Account.balance + data['value']
        print(acc_to_update.balance)

    income = Transaction()
    income.from_dict(data, user_id=user_id)
    db.session.add(income)
    db.session.commit()
    response = jsonify(income.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_user_transactions', user_id=income.user_id)
    return response


@bp.route('/users/<int:user_id>/expenses', methods=['POST'])
def create_expense(user_id):
    data = request.get_json() or {}

    if 'paid' in data and data['paid']:
        acc_to_update = Account.query.filter_by(id=data['account_id']).first()
        acc_to_update.balance = Account.balance - data['value']

    income = Transaction()
    income.from_dict(data, user_id=user_id)
    db.session.add(income)
    db.session.commit()
    response = jsonify(income.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_user_transactions', user_id=income.user_id)
    return response
    pass


@bp.route('/users/<int:user_id>/transactions', methods=['GET'])
def get_user_transactions(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    data = Transaction.to_collection_dict(Transaction.query.filter_by(user_id=user_id), page, per_page, 'api.get_user_transactions', user_id=user_id)
    return jsonify(data)


@bp.route('/users/<int:user_id>/incomes', methods=['GET'])
def get_user_incomes(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    data = Transaction.to_collection_dict(Transaction.query.filter_by(user_id=user_id, transaction_type=INCOME), page, per_page,
                                          'api.get_user_incomes', user_id=user_id)
    return jsonify(data)


@bp.route('/users/<int:user_id>/expenses', methods=['GET'])
def get_user_expenses(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 100)
    data = Transaction.to_collection_dict(Transaction.query.filter_by(user_id=user_id, transaction_type=EXPENSE), page, per_page,
                                          'api.get_user_incomes', user_id=user_id)
    return jsonify(data)


@bp.route('/transactions/<int:transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    return jsonify(Transaction.query.get_or_404(transaction_id).to_dict())


@bp.route('/transactions/<int:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    data = request.get_json() or {}

    already_paid = transaction.paid

    if 'paid' in data:
        acc_to_update = Account.query.filter_by(id=data['account_id']).first()
        # nao estava paga e agora foi paga
        if data['paid'] and not already_paid:
            if data['transaction_type'] == EXPENSE:
                acc_to_update.balance = Account.balance - data['value']
            else:
                acc_to_update.balance = Account.balance + data['value']
        # estava paga, mas foi desmarcada de como paga
        if not data['paid'] and already_paid:
            if data['transaction_type'] == EXPENSE:
                acc_to_update.balance = Account.balance + transaction.value
            else:
                acc_to_update.balance = Account.balance - transaction.value

    transaction.from_dict(data)
    db.session.commit()
    return jsonify(transaction.to_dict())

