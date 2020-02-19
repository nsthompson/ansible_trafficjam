#!/usr/bin/env python3

# Copyright: (c) 2020, World Wide Technology, All Rights Reserved
# Written By: Nick Thompson (nick.thompson@wwt.com)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: trafficjam_loopback_interfaces

short_description: This module is used to create, delete, and query information about Loopback Interfaces in the WWT ATC Tool TrafficJam

version_added: "2.9"

description:
    - "This module is used to create, delete, and query information about Loopback Interfaces in the WWT ATC Tool TrafficJam"

options:
    host:
        description:
            - Address for TrafficJam instance
        required: true
    port:
        description:
            - HTTP Port for TrafficJam instance
        required: false
        default: 80
    timeout:
        description:
            - HTTP Timeout
        required: false
        default: 10
    state:
        description:
            - Parameter to determine module behavior.
            - Use present or absent for adding / removing interfaces
            - Query will return all or specific interfaces and subinterfaces
        required: false
        default: query
        choices:
            - present
            - absent
            - query

    config:

    description:
        description:
            - Interface Description
        required: false
    v4_address:
        description:
            - IPV4 Address/Mask
        required: false
    v6_address:
        description:
            - IPV6 Address/Mask
        required: false
    vrf_id:
        description:
            - ID (integer) of the existing VRF
        required: false

author:
    - Nick Thompson (nick.thompson@wwt.com)
'''

EXAMPLES = '''
# Get Information about Loopback Interface
- name: Get Loopback Interface Information
  trafficjam_loopback_interfaces:
    host: trafficjam
    state: query

# Update Loopback Interface Settings
- name: Change Loopback Interface Settings
  trafficjam_loopback_interfaces:
    host: trafficjam
    state: present
    config:
      description: "Test Loopback Interface"
      v4_address: 1.1.1.1/24

# Delete Loopback Interface Settings
- name: Delete Loopback Interface Settings
  trafficjam_loopback_interfaces:
    host: trafficjam
    state: absent
    config:
      description: "Test Loopback Interface"
      v4_address: 1.1.1.1/24
'''

RETURN = '''
response:
    description: The Response Data from TrafficJam
    type: dict
    returned: always

status_code:
    description: The HTTP Status Code returned by TrafficJam
    type: int
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.wwt.trafficjam.plugins.module_utils.trafficjam import trafficjam_base_argspec, make_request, parse_query_return, process_response

def generate_url(_params):
    # Gather Parameters
    _state = _params['state']
    _host = _params['host']
    _port = _params['port']

    # Default _payload to None.  If required, this will be set below.
    _payload = None

    # Generate URL for Query Requests
    if _params['state'] == "query":
        # Generate URLs for Loopback Interface requests
        if (_params['config'] is None) or (_params['config'] is not None):
            _url = f"http://{_host}:{_port}/trafficjam/api/interfaces/loopback"
            _http_method = "get"

            # Construct a dictionary to return results with
            _response_dict = { "url": _url, "http_method": _http_method, "data": _payload }
            return _response_dict

    # Generate URL for Present Requests
    if _params['state'] == "present":
        # Generate URLs for Loopback Interface requests
        if (_params['config'] is not None) and ((_params['config']['description'] is not None or _params['config']['vrf_id'] is not None or _params['config']['v4_address'] is not None or _params['config']['v6_address'] is not None)):
            _url = f"http://{_host}:{_port}/trafficjam/api/interfaces/loopback"
            _http_method = "put"
            _payload = {
                "description": _params['config']['description'],
                "vrf_id": _params['config']['vrf_id'],
                "v4_address": _params['config']['v4_address'],
                "v6_address": _params['config']['v6_address']
                }

            # Construct a dictionary to return results with
            _response_dict = { "url": _url, "http_method": _http_method, "data": _payload }
            return _response_dict

    # Generate URL for Absent Requests
    if _params['state'] == "absent":
        if (_params['config'] is not None) and ((_params['config']['description'] is not None or _params['config']['vrf_id'] is not None or _params['config']['v4_address'] is not None or _params['config']['v6_address'] is not None)):
            _url = f"http://{_host}:{_port}/trafficjam/api/interfaces/loopback"
            _http_method = "delete"
            _payload = {
                "description": _params['config']['description'],
                "vrf_id": _params['config']['vrf_id'],
                "v4_address": _params['config']['v4_address'],
                "v6_address": _params['config']['v6_address']
                }

            # Construct a dictionary to return results with
            _response_dict = { "url": _url, "http_method": _http_method, "data": _payload }
            return _response_dict   
    
def run_module():
    #define available arguments/parameters a user can pass to the module
    module_args = trafficjam_base_argspec()

    config_spec = dict(
        description=dict(type='str', required=False),
        v4_address=dict(type='str', required=False),
        v6_address=dict(type='str', required=False),
        vrf_id=dict(type='int', required=False)
    )

    module_args.update(
        subinterface=dict(type='bool', required=False, default=False),
        state=dict(type='str', choices=['query', 'present', 'absent'], default='query'),
        config=dict(type='dict', options=config_spec)
    )

    # seed the result dict in the object
    # we primarily care about changed and the response data
    # change is if this module effectively modified the target
    # response is the data returned by TrafficJam
    # status_code is the HTTP status code returned by the requests module
    result = dict(
        changed=False,
        response='',
        status_code=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False,
        required_if=[
            ['state', 'present', ['config']],
            ['state', 'absent', ['config']]
        ]
    )

    # Generate the URL and HTTP Method based on Module Parameters
    url_response = generate_url(module.params)

    url = url_response['url']
    http_method = url_response['http_method']
    payload = url_response['data']

    # Generate the Request to the TrafficJam API
    response = make_request(http_method, url, payload, module.params['timeout'])

    # Exit the module passing results back to Ansible
    succeeded = process_response(response)
    
    # Manage States Returned to Ansible - If Query, Nothing will ever be changed.
    if succeeded and module.params['state'] == "query":
        result['changed'] = False
        result['failed'] = False
    elif succeeded:
        result['changed'] = True
        result['failed'] = False
    else:
        result['changed'] = False
        result['failed'] = True
    result['status_code'] = response['status_code']
    result['response'] = response['response']
    
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()