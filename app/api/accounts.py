# -*- coding: utf-8 -*-
from flask import jsonify, request, url_for
from app import db
from app.api.errors import bad_request
from app.models import User, Account
from app.api import bp
from app.api.auth import token_auth

@bp.route('/users/<int:user_id>/accounts', methods=['POST'])
def create_account(user_id):
    data = request.get_json() or {}
    if 'name' not in data or data['name'] == "":
        return bad_request('Deve informar um nome para a conta')
    if Account.query.filter_by(user_id=user_id, name=data['name'], account_type=data['account_type']).first():
        return bad_request('Você já tem uma conta com esse nome no mesmo tipo de conta')
    acc = Account()
    acc.from_dict(data, user_id=user_id)
    db.session.add(acc)
    db.session.commit()
    response = jsonify(acc.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_user_accounts', user_id=acc.user_id)
    return response

@bp.route('/accounts/<int:account_id>', methods=['GET'])
def get_account(account_id):
    return jsonify(Account.query.get_or_404(account_id).to_dict())

@bp.route('/users/<int:user_id>/accounts', methods=['GET'])
def get_user_accounts(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Account.to_collection_dict(Account.query.filter_by(user_id=user_id), page, per_page, 'api.get_user_accounts', user_id=user_id)
    return jsonify(data)

@bp.route('/accounts/<int:account_id>', methods=['PUT'])
def update_account(account_id):
    account = Account.query.get_or_404(account_id)
    data = request.get_json() or {}
    account.from_dict(data)
    db.session.commit()
    return jsonify(account.to_dict())