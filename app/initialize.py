import os
from flask import Flask, g, request
from app import config as config_module, api

config = config_module.get_config()

web_app = Flask(__name__)
web_app.config.from_object(config)

api.create_api(web_app)

def run():
    web_app.run(host='0.0.0.0', port=int(os.environ.get('PORTA', 33366)), debug=True)
