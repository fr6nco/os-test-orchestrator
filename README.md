# Test Orchestrator rest API

This tool is used to orchestrate test cases with dane and the os-proxy compontent. The location of test cases is configurable in the config files. Currently it points to **testcase_path = ./test_cases**

Configuration options:
Config is stored in the **./config** dir. Use the sample file to create a custom one. 

	[orchestrator]

	# listen = IP to listen on
	listen = 0.0.0.0

	# port = Port to listen on
	port = 8089

	# testcase_path = path to a directory, where test cases are stored
	testcase_path = ./test_cases

	# schema_path = path to a json schema to validate the config against
	schema_path = ./modules/test_orchestrator/testcase.schema

	# os_proxy_endpoint = URL where the OS proxy is running to perform test cases
	os_proxy_endpoint = http://localhost:8090/api/qos

	# dane_server_endpoint = URL where the DANE server is running
	dane_server_endpoint = http://localhost:8088


## Testcase Schema

The test cases must follow the desired schema. The current JSON schema may be found in the ./modules/test_orchestrator/testcase.schema. The values in this json file are validated against this schema and some further checks are performed too. To add a new test case, currently the application has to be reloaded as test cases are loaded and validated on start-up time.

###Testcase Example:

	{
	  "name": "testcase5",
	  "hosts": [
	    {
	      "name": "dane_server",
	      "ip": "172.16.4.9",
	      "lookup": "ip",
	      "primary_data_direction": "outgoing",
	      "tell_dane": true
	    }
	  ],
	  "bandwidths": [
        {
	      "name": "800mbit",
	      "bw": 800000
	    },
	    {
	      "name": "10mbit",
	      "bw": 10000
	    }
	  ],
	  "actions": [
	    {
	      "set": "bw",
	      "on": "dane_server",
	      "to": "10mbit",
	      "at": 60
	    },
	    {
	      "set": "bw",
	      "on": "dane_server",
	      "to": "800mbit",
	      "at": 120
	    }
	  ]
	}
Above example sets BW limit on dane server at IP 172.16.4.9 to 10 Mbits at the 60th second of the testcase on outgoing direction from server.
Sets the bandwidth to 800MBit (basically unlimited) at the second 120 for tha same hosts.
Bandwidth changes and availability are reported to the DANE endpoint.

The main json file contains 4 sections:
 * name - name of testcase, string
 * hosts - hosts to be policied
 * actions - actions to taken
 * bandwidths - values to be set

#### Hosts:
Array
Properties:
 * name: Name of host - required
 * lookup: enum [ip, fqdn] - required
 * ip: IP address of host - required if ip is defined in lookup
 * fqdn: domain name (fqdn) - required if fqdn is defined in lookup. fqdn is translated to ip in validation section
 * primary_data_direction: incoming or outgoing, defines which is the main data flow. eg outgoing for a web server - optional
 * tell_dane: true or false, defines whether the bandwidth limitation should be sent to dane endpoint. Applies only for server - optional

#### bandwidths
Array
Properties:
 * name: name of entry - required
 * bw: bandwidth, in kbits/s - required

#### Actions
Array
Properties:
 * set: enum ["bw"]; action type - required
 * on: host to policy. Must be matched in the hosts section - required
 * to: value to set to. If enum type "bw", to must match a bandwidth in the bandwidths section by name - required
 * at: time when to apply the action. In seconds from the beginning of the test - required
 * direction: Set the direction on which to apply the action enum ["incoming", "outgoing"] - required only if primary_data_direction is not set at the host section for the "on" parameter



## Get list of Tests

### Request

`GET /tests`

### Response

    {
	    "tests": 
	    [
	        {
				"name": "testcase5",
				"hosts": [
					{
						"name": "dane_server",
						"ip": "172.16.4.9",
						"primary_data_direction": "outgoing",
						"tell_dane": true
					}
				],
				"bandwidths": [
					{
						"name": "800mbit",
						"bw": 800000
					},
					{
						"name": "10mbit",
						"bw": 10000
					}
				],
				"actions": [
					{
						"set": "bw",
						"on": "dane_server",
						"to": "10mbit",
						"at": 60
					},
					{
						"set": "bw",
						"on": "dane_server",
						"to": "800mbit",
						"at": 120
					}
				]
			}
		]
	}

## Get a single test case by name

### Request

`GET /test/<string:name>`

### Response

	{
	  "name": "testcase5",
	  "hosts": [
	    {
	      "name": "dane_server",
	      "ip": "172.16.4.9",
	      "primary_data_direction": "outgoing",
	      "tell_dane": true
	    }
	  ],
	  "bandwidths": [
        {
	      "name": "800mbit",
	      "bw": 800000
	    },
	    {
	      "name": "10mbit",
	      "bw": 10000
	    }
	  ],
	  "actions": [
	    {
	      "set": "bw",
	      "on": "dane_server",
	      "to": "10mbit",
	      "at": 60
	    },
	    {
	      "set": "bw",
	      "on": "dane_server",
	      "to": "800mbit",
	      "at": 120
	    }
	  ]
	}

## Start a testcase

### Request

`POST /test/<string:name>`

    body: {}

### Response

    {
  	  "test1": "Test case started"
	}
