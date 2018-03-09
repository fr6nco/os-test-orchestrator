from flask import Flask
from flask_restful import Api
from resources.test import TestList, Test
from gevent import monkey
monkey.patch_all()

import ConfigParser
Config = ConfigParser.ConfigParser()
Config.read('./config/config.conf')

app = Flask(__name__)
api = Api(app)

api.add_resource(Test, '/test/<string:test_name>')
api.add_resource(TestList, '/tests')

if __name__ == '__main__':
    app.run(debug=False, host=Config.get('orchestrator', 'listen'), port=int(Config.get('orchestrator', 'port')))

