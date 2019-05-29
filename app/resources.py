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
        self.me = getattr(g, 'user_entity', None)
        if self.me is None and self.logged_user is not None:
            self.me = domain.User.create_with_logged(self.logged_user)
        if self.me is not None:
            self.me.entity_key = self.entity_key
            self.me.resource_key = self.resource_key


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
    def cookies(self):
        username = request.cookies.get('baseUserName', None)
        token = request.cookies.get('baseUserToken', 'null')
        return {'baseUserName': username, 'baseUserToken': token}

    @property
    def headers(self):
        return request.headers

    @property
    def logged_user(self):
        return getattr(g, 'user', None)

    def return_not_allowed(self):
        return self.response({'result': 'Method not allowed'}), 405

    def return_unexpected_error(self, ex):
        return self.response({'result': 'error', 'exception': str(ex)}), 500

    def response(self, data_dict):
        return self.transform_key(data_dict, self.snake_to_camel)

    def get_list(self, **kwargs):
        try:
            entity_list = self.me.get_list(self.payload, **kwargs)
            return [self.response(entity.as_dict(compact=self.list_compact)) for entity in entity_list]
        except Exception as ex:
            return self.return_unexpected_error(ex)

    def get_item(self, **kwargs):
        try:
            return self.response(self.me.get_item(**kwargs).as_dict())
        except self.me.EntityNotExist:
            return "Item doesn't exist", 404
        except Exception as ex:
            return self.return_unexpected_error(ex)

    @login_required
    def get(self, **kwargs):
        if 'GET' not in self.http_methods_allowed:
            return self.return_not_allowed()
        if kwargs.get('{}_id'.format(self.entity_key)) is None:
            return self.get_list(**kwargs)
        else:
            return self.get_item(**kwargs)

    @login_required
    def post(self, **kwargs):
        if 'POST' not in self.http_methods_allowed:
            return self.return_not_allowed()
        try:
            created = self.me.create_new_entity(self.payload, **kwargs)
            return self.response(created.as_dict()), 201
        except self.me.InvalidEntityData as ex:
            return self.response({'erro': 'Invalid data.', 'internal_code': ex.message}), 400
        except self.me.EntityAlreadyExist as ex:
            return {'erro': 'already-exist', 'exception': ex.message}, 400
        except Exception as ex:
            return self.return_unexpected_error(ex)

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

    @login_required
    def put(self, **kwargs):
        if 'PUT' not in self.http_methods_allowed:
            return self.return_not_allowed()
        try:
            payload = self.payload
            file_attached = self.__extract_file_attached()
            if file_attached is not None:
                payload = {
                    'uploading': True,
                    'file_attached': file_attached
                }
            updated = self.me.update(payload, **kwargs)
            if updated:
                return self.response(updated.as_dict()), 200
            return self.response({'result': 'ERROR'}), 500
        except self.me.InvalidEntityData as ex:
            return self.response({'erro': 'Invalid data.', 'internal_code': ex.message}), 400
        except self.me.EntityAlreadyExist as ex:
            return {'erro': 'already-exist', 'exception': ex.message}, 400
        except Exception as ex:
            return self.return_unexpected_error(ex)

    @login_required
    def delete(self, **kwargs):
        if 'DELETE' not in self.http_methods_allowed:
            return self.return_not_allowed()
        try:
            self.me.delete(**kwargs)
            return {'resultado': 'OK'}, 204
        except self.me.CouldNotDelete as ex:
            return self.response({'erro': 'Could not Delete', 'internal_code': ex.message}), 400
        except self.me.WhoDaHellYouThinkYouAre as ex:
            return self.response({'erro': 'Could not Delete', 'internal_code': 'its_not_yours'}), 400
        except Exception as ex:
            return self.return_unexpected_error(ex)


class AccountResource(ResourceBase):
    http_methods_allowed = ['GET', 'POST', 'PUT']
    entity = domain.Account

    def get(self, account_id=None, user_id=None):
        try:
            # self.entity.create_new(self.payload)
            domain.Account.get_user_accounts(21)
            # return self.response({'result': 'success', 'data': account_data})

            # if account_id:
            #     account_data = domain.Account.get_account(account_id)
            #     return self.response({'result': 'success', 'data': account_data})
            #
            # if user_id:
            #     user_accounts = domain.Account.get_user_accounts(user_id)
            #     return self.response({'result': 'success', 'data': user_accounts})
            user_accounts = {
                'name': "CC Itau",
                'balance': 221.58
            }
            return self.response(user_accounts)
            # return self.response({'result': 'GET OK', 'data': 'nothing to return'})
        except Exception as ex:
            return self.return_unexpected_error(ex)

    # def post(self, user_id):
    #     try:
    #         if user_id:
    #             # TODO: passar nome da conta e tipo da conta no payload
    #             account_created = domain.Account.create_account(user_id)
    #             return self.response({'result': 'success', 'data': account_created})
    #
    #         return self.response({'result': 'POST OK', 'data': 'nothing to return'})
    #     except Exception as ex:
    #         return self.return_unexpected_error(ex)

    # def put(self, account_id):
    #     try:
    #         if account_id:
    #             account_data = domain.Account.update_account(account_id)
    #             return self.response({'result': 'success', 'data': account_data})
    #
    #         return self.response({'result': 'PUT OK', 'data': 'nothing to return'})
    #     except Exception as ex:
    #         return self.return_unexpected_error(ex)

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

    def get(self):
        try:
            users = self.entity.list_all()
            users_dict = {}
            for user in users:
                users_dict[str(user.id)] = {
                    'name': user.name,
                    'email': user.email
                }

            return self.response({'result': 'success', 'data': users_dict})
        except Exception as ex:
            return self.return_unexpected_error(ex)

    def post(self):
        try:
            self.entity.create_new(self.payload)
            return self.response({'result': 'success', 'data': 'user created'})
        except Exception as ex:
            return self.return_unexpected_error(ex)


class LoginResource(ResourceBase):
    http_methods_allowed = ['POST']
    entity = domain.User

    def post(self):
        try:
            user = self.entity.create_for_login(self.payload)
            if user.is_correct:
                g.user = user.as_dict()
                g.current_token = user.generate_auth_token()
                return {'logged': True}, 200
        except Exception:
            return {'result': 'Not Authorized'}, 401
        return {'result': 'Not Authorized'}, 401


class MeResource(ResourceBase):
    http_methods_allowed = ['GET', 'PUT']

    @login_required
    def get(self):
        try:
            return self.response(self.me.as_dict())
        except Exception as ex:
            return self.return_unexpected_error(ex)

    @login_required
    def put(self):
        try:
            self.me.update_me(self.payload)
            return self.response({'result': 'OK'})
        except Exception as ex:
            return self.return_unexpected_error(ex)


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
