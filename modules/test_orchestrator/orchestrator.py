import json
import os
import gevent
from jsonschema.validators import validate
from jsonschema.exceptions import ValidationError

import logging
LOGGER = logging.getLogger(__name__)

class TestHandler():
    def __init__(self, path='modules/test_orchestrator/test_cases'):
        self.tests = []

        #TODO validate if path exists
        for file in os.listdir(path):
            testcase = TestCase(path=path + '/' + file)
            if testcase.valid:
                LOGGER.info('Testcase  '+ str(testcase) + ' valid, adding to list')
                self.tests.append(testcase)
            else:
                LOGGER.error('Testcase is invalid')

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
        return None

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
            LOGGER.error(str(e))
            self.valid = False
        except ValueError as e:
            LOGGER.error(str(e))
            self.valid = False

    def validate_data(self):
        if not self.valid:
            return

        try:
            validate(self.data, self.schema)
        except ValidationError as e:
            LOGGER.error(e)
            self.valid = False
            return

        self.bandwidths = self.data['bandwidths']
        self.hosts = self.data['hosts']
        self.actions = self.data['actions']
        self.name = self.data['name']

        for action in self.actions:
            if len(filter(lambda e: e['name'] == action['on'], self.hosts)) == 0 or \
                     len(filter(lambda e: e['name'] == action['to'], self.bandwidths)) == 0:
                LOGGER.error('action ' + str(action) + ' invalid in file ' + self.name + ' ' + self.path)
                self.valid = False

    def get_host_ip(self, host_name):
        entries = filter(lambda e: e["name"] == host_name, self.hosts)
        return entries[0]["ip"]

    def get_bw_in_kbps(self, bw_name):
        entries = filter(lambda e: e["name"] == bw_name, self.bandwidths)
        return entries[0]["bw"] / 1000

    def executeEvent(self, action, idx):

        if 'for' in action:
            LOGGER.debug('Executing action: Set ' + action['set'] + ' to ' + action['to'] + ' on ' + action[
                'on'] + ' for ' + str(action['for']) + ' seconds')
        else:
            LOGGER.debug('Executing action: Set ' + action['set'] + ' to ' + action['to'] + ' on ' + action['on'])

        if idx == "last":
            LOGGER.debug('Test case ' + self.name + ' Finished')
            self.state = 'FINISHED'

    def __str__(self):
        return self.name + " from " + self.path + ' state ' + self.state

    def startEvents(self):
        LOGGER.info('Starting test case {}'.format(self.name))
        timer = 0
        self.state = 'RUNNING'

        for idx, action in enumerate(self.actions):
            if idx == 0:
                g = gevent.spawn_later(timer, self.executeEvent, action, "first")
            elif idx == len(self.actions) - 1:
                g = gevent.spawn_later(timer, self.executeEvent, action, "last")
            else:
                g = gevent.spawn_later(timer, self.executeEvent, action, "middle")

            self.eventStack.append(g)

            if 'for' in action:
                timer += action['for']

