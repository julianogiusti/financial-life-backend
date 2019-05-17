"""
This module define all the api endpoints
"""

from flask_restful import Api


def create_api(app):
    """
    Used when creating a Flask App to register the REST API and its resources
    """
    from app import resources
    api = Api(app)

    # users
    api.add_resource(resources.UserResource, '/api/users')
    api.add_resource(resources.LoginResource, '/api/login')
    api.add_resource(resources.MeResource, '/api/me')

    # manage accounts
    # api.add_resource(resources.AccountResource,
    #     '/api/users/<int:user_id>/accounts',
    #     '/api/accounts/<int:account_id>'
    #     )
    #
    # # manage transfers
    # api.add_resource(resources.TransferResource,
    #     '/api/users/<int:user_id>/transfers',
    #     '/api/transfers/<int:transfer_id>',
    #     '/api/accounts/<int:account_id>/transfers'
    #     )
    #
    # # manage transactions
    # api.add_resource(resources.TransactionResource,
    #     '/api/users/<int:user_id>/incomes',
    #     '/api/users/<int:user_id>/expenses',
    #     '/api/users/<int:user_id>/transactions',
    #     '/api/transactions/<int:transaction_id>'
    #     )

    api.add_resource(resources.HealthcheckResource,
                     '/api/healthcheck',
                     '/api/healthcheck/<string:service>')


def authenticate_api(token):
    from app import config
    return token == config.get_config().API_TOKEN
