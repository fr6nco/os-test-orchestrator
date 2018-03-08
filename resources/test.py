from flask_restful import fields, marshal_with, Resource, abort
from modules.test_orchestrator.orchestrator import TestHandler

import logging
LOGGER = logging.getLogger(__name__)

test_resource_host_fields = {
    'name': fields.String,
    'ip': fields.String
}

test_resource_bandwidth_fields = {
    'name': fields.String,
    'bw': fields.Integer
}

test_resource_action_fields = {
    'set': fields.String,
    'on': fields.String,
    'to': fields.String,
    'direction': fields.String,
    'at': fields.Integer,
}

test_resource_fields = {
    'name': fields.String,
    'path': fields.String,
    'valid': fields.Boolean,
    'hosts': fields.List(fields.Nested(test_resource_host_fields)),
    'bandwidths': fields.List(fields.Nested(test_resource_bandwidth_fields)),
    'actions': fields.List(fields.Nested(test_resource_action_fields)),
    'state': fields.String
}

TESTS = TestHandler()


class Test(Resource):
    @marshal_with(test_resource_fields)
    def get(self, test_name):
        test = TESTS.getTest(name=test_name)
        return test if test is not None else abort(404, message="Test case {} doesn't exist".format(test_name))

    def post(self, test_name):
        events = TESTS.orchestrateTest(name=test_name)
        if events:
            LOGGER.info('Test case started')
            return {test_name: 'Test case started'}
        else:
            LOGGER.info('Test case not found')
            abort(404, message="Test case {} doesn't exist".format(test_name))


class TestList(Resource):
    @marshal_with(test_resource_fields, envelope='tests')
    def get(self, **kwargs):
        return TESTS.getTests()