from flask import Flask
from flask_restful import Api
from resources.test import TestList, Test
from gevent import monkey, wsgi
monkey.patch_all()

app = Flask(__name__)
api = Api(app)

api.add_resource(Test, '/test/<string:test_name>')
api.add_resource(TestList, '/tests')


if __name__ == '__main__':
    app.run(debug=False)
    server = wsgi.WSGIServer(('127.0.0.1', 5000), app)

