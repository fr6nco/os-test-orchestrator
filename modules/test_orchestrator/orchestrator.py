import json
import os
import gevent
import requests
import socket
from jsonschema.validators import validate
from jsonschema.exceptions import ValidationError

import ConfigParser
Config = ConfigParser.ConfigParser()
Config.read('./config/config.conf')

import logging
LOGGER = logging.getLogger(__name__)

class TestHandler():
    def __init__(self):
        self.path = Config.get('orchestrator', 'testcase_path')
        self.tests = []

        for file in os.listdir(self.path):
            testcase = TestCase(path=self.path + '/' + file)
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

class TestCase:
    def __init__(self, path):
        self.SCHEMA_PATH = Config.get('orchestrator', 'schema_path')
        self.OS_PROXY_ENDPOINT = Config.get('orchestrator', 'os_proxy_endpoint')
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

        self.loaddata()
        self.validate_data()

    def loaddata(self):
        try:
            with open(self.path) as f_content:
                self.data = json.loads(f_content.read())
            with open(self.SCHEMA_PATH) as s_content:
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
                     len(filter(lambda e: e['name'] == action['to'] or action['to'] is None, self.bandwidths)) == 0:
                LOGGER.error('action ' + str(action) + ' invalid in file ' + self.name + ' ' + self.path)
                self.valid = False

        for host in self.hosts:
            if host['lookup'] == 'ip' and 'ip' not in host or host['lookup'] == 'fqdn' and 'fqdn' not in host:
                LOGGER.error('host ' + str(host) + ' invalid in file ' + self.name + ' ' + self.path)
                LOGGER.error('set IP or FQDN according to Lookup variable')
                self.valid = False

            if self.valid and host['lookup'] == 'fqdn':
                try:
                    host['ip'] = socket.gethostbyname(host['fqdn'])
                except socket.gaierror as e:
                    LOGGER.error(str(e))
                    LOGGER.error('FQDN unresolved')
                    self.valid = False


    def assignQosRule(self, name, action_type, direction, max_kbps):

        data = {
            'action': 'add',
            'type': action_type,
            'direction': direction,
            'max_kbps': max_kbps,
            'max_burst_kbps': 0
        }

        r = requests.post(self.OS_PROXY_ENDPOINT + '/policy/' + name, data=data)

        if r.status_code == 200:
            LOGGER.debug('Policy set successfully')
            LOGGER.debug(str(r.json()))
        else:
            LOGGER.error('Failed to set policy' + r.text)

    def unassignQosRule(self, name, action_type, direction):
        data = {
            'action': 'delete',
            'type': action_type,
            'direction': direction
        }

        r = requests.post(self.OS_PROXY_ENDPOINT + '/policy/' + name, data=data)

        if r.status_code == 200:
            LOGGER.debug('Policy unset successfully')
        else:
            LOGGER.error('Failed to unset policy' + r.text)

    def tellDane(self, bandwidth=None):
        if bandwidth:
            url = Config.get('orchestrator', 'dane_server_endpoint') + '/api/bandwidth'

            data = {
                'bw': bandwidth * 1000
            }
            res = requests.put(url, data=data)

            if res.status_code == 200:
                LOGGER.debug('Server speed status updated on DANE. Speed set to ' + str(data['bw']))
            else:
                LOGGER.error('Failed to inform dane about the speed.')
                LOGGER.error(res.text)
        else:
            url = Config.get('orchestrator', 'dane_server_endpoint') + '/api/reset'

            res = requests.post(url)

            if res.status_code == 200:
                LOGGER.debug('Reset called on DANE')
            else:
                LOGGER.error('Failed to inform dane about the speed.')
                LOGGER.error(res.text)


    def executeEvent(self, action, idx):
        LOGGER.debug('Executing action: Set ' + action['set'] + ' to ' + str(action['to']) + ' on ' + action['on'])

        for host in self.hosts:
            if host['name'] == action['on']:
                if action['to'] is None:
                    if 'direction' in action:
                        self.unassignQosRule(host['name'], action['set'], action['direction'])
                    else:
                        self.unassignQosRule(host['name'], action['set'], host['primary_data_direction'])
                    if 'tell_dane' in host and host['tell_dane']:
                        self.tellDane()
                else:
                    for bw in self.bandwidths:
                        if bw['name'] == action['to']:
                            if 'direction' in action:
                                self.assignQosRule(host['name'], action['set'], action['direction'], bw['bw'])
                            else:
                                self.assignQosRule(host['name'], action['set'], host['primary_data_direction'], bw['bw'])
                            if 'tell_dane' in host and host['tell_dane']:
                                self.tellDane(bw['bw'])

        if idx == "last":
            LOGGER.debug('Test case ' + self.name + ' Finished')
            self.state = 'FINISHED'
            self.deletePolicies()

    def __str__(self):
        return self.name + " from " + self.path + ' state ' + self.state

    def loadPolicies(self):
        for host in self.hosts:
            r = requests.post(self.OS_PROXY_ENDPOINT + '/policy', data=host)

            if r.status_code == 200:
                LOGGER.debug(str(r.json()))
            else:
                LOGGER.error("Failed to load policy to openstack " + r.text)

    def deletePolicies(self):
        for host in self.hosts:
            r = requests.delete(self.OS_PROXY_ENDPOINT + '/policy/' + host['name'])

            if r.status_code == 200:
                LOGGER.debug('Policy deleted')
            else:
                LOGGER.error('Failed to delete policy' + r.text)


    def startEvents(self):
        LOGGER.info('Starting test case {}'.format(self.name))

        self.deletePolicies()
        self.loadPolicies()

        self.state = 'RUNNING'

        for idx, action in enumerate(self.actions):
            if idx == 0:
                g = gevent.spawn_later(action['at'], self.executeEvent, action, "first")
            elif idx == len(self.actions) - 1:
                g = gevent.spawn_later(action['at'], self.executeEvent, action, "last")
            else:
                g = gevent.spawn_later(action['at'], self.executeEvent, action, "middle")

            self.eventStack.append(g)


