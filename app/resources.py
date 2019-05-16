from functools import wraps
import re

from flask import request, g, Response
from flask_restful import Resource

from app import config as config_module, domain
# from app.domain import Account, User

config = config_module.get_config()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        authenticated = getattr(g, 'authenticated', False)
        if not authenticated:
            return Response('{"result": "Not Authorized"}', 401, content_type='application/json')
        return f(*args, **kwargs)
    return decorated_function

def not_allowed(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return Response('{"result": "Method not allowed"}', 405, content_type='application/json')
    return decorated_function


class ResourceBase(Resource):
    http_methods_allowed = ['GET', 'POST', 'PUT', 'DELETE']
    entity_key = None
    resource_key = None
    list_compact = True

    def __init__(self):
        super(ResourceBase, self).__init__()
        self.__payload = None


    @staticmethod
    def camel_to_snake(name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


    @staticmethod
    def snake_to_camel(name):
        result = []
        for index, part in enumerate(name.split('_')):
            if index == 0:
                result.append(part.lower())
            else:
                result.append(part.capitalize())
        return ''.join(result)


    def transform_key(self, data, method):
        if isinstance(data, dict):
            return {method(key): self.transform_key(value, method) for key, value in data.items()}
        if isinstance(data, list):
            for index, item in enumerate(data):
                if isinstance(item, dict):
                    data[index] = {method(key): self.transform_key(value, method) for key, value in item.items()}
        return data


    @property
    def payload(self):
        payload = {}
        if request.json:
            payload.update(self.transform_key(request.json, self.camel_to_snake))
        if request.form:
            payload.update(self.transform_key(request.form, self.camel_to_snake))
        if request.args:
            payload.update(self.transform_key(request.args, self.camel_to_snake))
        if request.files:
            payload['attachment'] = request.files
        return payload


    @property
    def headers(self):
        return request.headers


    def return_not_allowed(self):
        return self.response({'result': 'Method not allowed'}), 405


    def return_unexpected_error(self, ex):
        return self.response({'result': 'error', 'exception': str(ex)}), 500


    def response(self, data_dict):
        return self.transform_key(data_dict, self.snake_to_camel)


    def __extract_file_attached(self):
        try:
            if 'attachment' in self.payload:
                what_i_need = ['creator_id', 'created_at', 'file_attached']
                attachments_results = []
                for attachment in self.payload['attachment'].itervalues():
                    key = attachment.name.replace('[file]', '')
                    attachment_result = {}
                    for props in what_i_need:
                        attachment_result[props] = self.payload['{}[{}]'.format(key, props)]
                    attachment_result['file'] = {'name': attachment.filename, 'stream': attachment.stream}
                    attachments_results.append(attachment_result)
                return attachments_results
        except Exception as ex:
            pass
        return None


# class AccountResource(ResourceBase):
#     http_methods_allowed = ['GET', 'POST', 'PUT']
#
#     def get(self, account_id=None, user_id=None):
#         try:
#             if account_id:
#                 account_data = Account.get_account(account_id)
#                 return self.response({'result': 'success', 'data': account_data})
#
#             if user_id:
#                 user_accounts = Account.get_user_accounts(user_id)
#                 return self.response({'result': 'success', 'data': user_accounts})
#
#             return self.response({'result': 'GET OK', 'data': 'nothing to return'})
#         except Exception as ex:
#             return self.return_unexpected_error(ex)
#
#     def post(self, user_id):
#         try:
#             if user_id:
#                 # TODO: passar nome da conta e tipo da conta no payload
#                 account_created = Account.create_account(user_id)
#                 return self.response({'result': 'success', 'data': user_accounts})
#
#             return self.response({'result': 'POST OK', 'data': 'nothing to return'})
#         except Exception as ex:
#             return self.return_unexpected_error(ex)
#
#     def put(self, account_id):
#         try:
#             if account_id:
#                 account_data = Account.update_account(account_id)
#                 return self.response({'result': 'success', 'data': account_data})
#
#             return self.response({'result': 'PUT OK', 'data': 'nothing to return'})
#         except Exception as ex:
#             return self.return_unexpected_error(ex)
#
#
# class TransferResource(ResourceBase):
#     http_methods_allowed = ['GET', 'POST']
#
#     def get(self, account_id=None, transfer_id=None):
#         try:
#             if account_id:
#                 account_transfers = Transfer.get_account_transfers(account_id)
#                 return self.response({'result': 'success', 'data': account_transfers})
#
#             if transfer_id:
#                 transfer_data = Transfer.get_transfer(transfer_id)
#                 return self.response({'result': 'success', 'data': transfer_data})
#
#             return self.response({'result': 'GET OK', 'data': 'nothing to return'})
#         except Exception as ex:
#             return self.return_unexpected_error(ex)
#
#     def post(self, user_id):
#         try:
#             if user_id:
#                 # TODO: passar contas da transferencia no payload (from to)
#                 transfer_realized = Transfer.create_transfer(user_id)
#                 return self.response({'result': 'success', 'data': transfer_realized})
#
#             return self.response({'result': 'POST OK', 'data': 'nothing to return'})
#         except Exception as ex:
#             return self.return_unexpected_error(ex)
#
#
# class TransactionResource(ResourceBase):
#     http_methods_allowed = ['GET', 'POST', 'PUT']
#
#     def get(self, transaction_id=None, user_id=None):
#         try:
#             if transaction_id:
#                 transaction_data = Transaction.get_transaction(transaction_id)
#                 return self.response({'result': 'success', 'data': transaction_data})
#
#             if user_id:
#                 # TODO: passar se quer despesas ou receitas no payload
#                 user_incomes = Transaction.get_user_incomes(user_id)
#                 user_expenses = Transaction.get_user_expenses(user_id)
#                 return self.response({'result': 'success', 'data': 'user_something'})
#
#             return self.response({'result': 'GET OK', 'data': 'nothing to return'})
#         except Exception as ex:
#             return self.return_unexpected_error(ex)
#
#     def post(self, user_id):
#         try:
#             if user_id:
#                 # TODO: passar se cria despesa ou receita
#                 income = Transaction.create_income(user_id)
#                 expense = Transaction.create_expense(user_id)
#                 return self.response({'result': 'success', 'data': 'money_in_or_out'})
#
#             return self.response({'result': 'POST OK', 'data': 'nothing to return'})
#         except Exception as ex:
#             return self.return_unexpected_error(ex)
#
#     def put(self, transaction_id):
#         try:
#             if transaction_id:
#                 transaction_data = Transaction.update_transaction(transaction_id)
#                 return self.response({'result': 'success', 'data': transaction_data})
#
#             return self.response({'result': 'PUT OK', 'data': 'nothing to return'})
#         except Exception as ex:
#             return self.return_unexpected_error(ex)


class UserResource(ResourceBase):
    http_methods_allowed = ['GET', 'POST', 'PUT']
    entity = domain.User

    # def get(self, user_id=None):
    #     try:
    #         if user_id:
    #             user_data = domain.User.get_user(user_id)
    #             return self.response({'result': 'success', 'data': user_data})
    #         else:
    #             users = domain.User.get_users()
    #             return self.response({'result': 'success', 'data': users})
    #
    #         return self.response({'result': 'GET OK', 'data': 'nothing to return'})
    #     except Exception as ex:
    #         return self.return_unexpected_error(ex)

    def post(self):
        try:
            self.entity.create_new(self.payload)
            return self.response({'result': 'success', 'data': 'user created'})
        except Exception as ex:
            return self.return_unexpected_error(ex)

    # def put(self, user_id=None):
    #     try:
    #         if user_id:
    #             user_updated = User.update_user(user_id)
    #             return self.response({'result': 'success', 'data': user_updated})
    #
    #         return self.response({'result': 'PUT OK', 'data': 'nothing to return'})
    #     except Exception as ex:
    #         return self.return_unexpected_error(ex)


class HealthcheckResource(Resource):
    def get(self, service=None):
        if service is None:
            return {"result": "OK"}, 200
        else:
            if service == 'database':
                try:
                    return {"result": "OK"}, 200
                except:
                    return {"result": "NOT"}, 200
