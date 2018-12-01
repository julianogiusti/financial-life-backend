from flask import Blueprint
from flask_cors import CORS

bp = Blueprint('api', __name__)

CORS(bp, resources=r'/api/*')

from app.api import users, accounts, transfers, transactions, errors, tokens
