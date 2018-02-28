from flask import Flask
from flask_restful import Api
import resources.test
from resources.test import TestList, Test

app = Flask(__name__)
api = Api(app)

api.add_resource(Test, '/test/<string:test_name>')
api.add_resource(TestList, '/tests')

if __name__ == '__main__':
    app.run(debug=False)