import json
import os
from jsonschema.validators import validate
from jsonschema.exceptions import ValidationError


class TestHandler:
    def __init__(self, path='modules/test_orchestrator/test_cases'):
        self.tests = []

        #TODO validaet if path exists
        for file in os.listdir(path):
            testcase = TestCase(path=path + '/' + file)
            if testcase.valid:
                print 'Testcase  '+ str(testcase) + ' valid, adding to list'
                self.tests.append(testcase)
            else:
                print 'Testcase is invalid'

    def getTests(self):
        return self.tests

    def getTestsObj(self):
        tests = {}
        tests['tests'] = []
        for test in self.tests:
            tests['tests'].append(test.data)
        return tests

    def getTest(self, name):
        for test in self.tests:
            if test.name == name:
                return test
        return None

    def orchestrateTest(self, name):
        for test in self.tests:
            if test.name == name:
                test.startEvents()
                return test.eventStack


#TODO Move to config file
SCHEMA_PATH = './modules/test_orchestrator/testcase.schema'


class TestCase:
    def __init__(self, path):
        self.path = path
        self.valid = True
        self.schema = ""
        self.data = {}
        self.hosts = []
        self.bandwidths = []
        self.actions = []
        self.name = ""
        self.eventStack = []
        self.state = 'INIT'
        self.curr_bw_rule_id ="" # TODO this is a bit hacky, assumes only one rule is present and modifiedd

        self.loaddata()
        self.validate_data()

    def loaddata(self):
        try:
            with open(self.path) as f_content:
                self.data = json.loads(f_content.read())
            with open(SCHEMA_PATH) as s_content:
                self.schema = json.loads(s_content.read())
        except IOError as e:
            print str(e)
            self.valid = False
        except ValueError:
            print ValueError
            self.valid = False

    def validate_data(self):
        if not self.valid:
            return

        try:
            validate(self.data, self.schema)
        except ValidationError:
            print ValidationError.message
            self.valid = False
            return

        self.bandwidths = self.data['bandwidths']
        self.hosts = self.data['hosts']
        self.actions = self.data['actions']
        self.name = self.data['name']

        for action in self.actions:
            if len(filter(lambda e: e['name'] == action['on'], self.hosts)) == 0 or \
                     len(filter(lambda e: e['name'] == action['to'], self.bandwidths)) == 0:
                print 'action ' + str(action) + ' invalid in file ' + self.name + ' ' + self.path
                self.valid = False