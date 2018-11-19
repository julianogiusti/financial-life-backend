# -*- coding: utf-8 -*-
from flask import jsonify, request, url_for
from app import db
from app.api.errors import bad_request
from app.models import User, Account, Transfer
from app.api import bp
from app.api.auth import token_auth


@bp.route('/users/<int:user_id>/transfers', methods=['POST'])
def create_transfer(user_id):
    data = request.get_json() or {}
    if 'from_account' not in data or 'to_account' not in data:
        return bad_request('Deve informar as duas contas para a transferência')

    from_acc = Account.query.filter_by(id=data['from_account']).first()
    to_acc = Account.query.filter_by(id=data['to_account']).first()

    from_acc.balance = Account.balance - data['amount']
    to_acc.balance = Account.balance + data['amount']

    transfer = Transfer()
    transfer.from_dict(data)
    db.session.add(transfer)
    db.session.commit()
    response = jsonify(transfer.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_user_accounts', user_id=user_id)
    return response

@bp.route('/transfers/<int:transfer_id>', methods=['GET'])
def get_transfer(transfer_id):
    return jsonify(Transfer.query.get_or_404(transfer_id).to_dict())

@bp.route('/users/<int:user_id>/transfers', methods=['GET'])
def get_user_transfers(user_id):
    """
    EM SQL:
        select * from transfer t
        join account ac
            on ac.id = t.from_account
        join user u
            on u.id = ac.user_id
        where u.id = 2
        order by transfer_date
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)

    data = Transfer.to_collection_dict(Transfer.query, page, per_page, 'api.get_user_transfers', user_id=user_id)
    return jsonify(data)