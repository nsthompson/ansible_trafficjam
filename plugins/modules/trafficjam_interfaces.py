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
module: trafficjam_interfaces

short_description: This module is used to query information about all Interfaces in the WWT ATC Tool TrafficJam

version_added: "2.9"

description:
    - "This module is used to query information about all Interfaces in the WWT ATC Tool TrafficJam"

options:
    host:
        description:
            - Address for TrafficJam instance
        required: true
    port:
        description:
            - HTTP Port for TrafficJam instance.  Default is 80.
        required: false
    timeout:
        description:
            - HTTP Timeout.  Default is 10s.
        required: false
    state:
        description:
            - Parameter to determine module behavior.  (query) - Default: query
        required: false

author:
    - Nick Thompson (nick.thompson@wwt.com)
'''

EXAMPLES = '''
# Get Information from all TrafficJam Interfaces
- name: Get Interface Information
  trafficjam_interfaces:
    host: trafficjam
    state: query
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
from ansible_collections.wwt.trafficjam.plugins.module_utils.trafficjam import trafficjam_base_argspec, make_request, process_response


def generate_url(_params):
    # Gather Parameters
    _state = _params['state']
    _host = _params['host']
    _port = _params['port']

    # Default _payload to None.  If required, this will be set below.
    _payload = None

    # Generate URL for Query Requests
    if _state == "query":
        _url = f"http://{_host}:{_port}/trafficjam/api/interfaces"
        _http_method = "get"

        # Construct a dictionary to return results with
        _response_dict = {"url": _url, "http_method": _http_method, "data": _payload}
        return _response_dict


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = trafficjam_base_argspec()

    module_args.update(
        state=dict(type='str', choices=['query'], default='query')
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
        supports_check_mode=False
    )

    # Generate the URL, HTTP Method, and Optional Payload based on Module Parameters
    url_response = generate_url(module.params)

    url = url_response['url']
    http_method = url_response['http_method']
    payload = url_response['data']

    # Generate the Request to the TrafficJam API
    response = make_request(http_method, url, payload, module.params['timeout'])

    # Exit the module passing results back to Ansible
    succeeded = process_response(response)

    # Manage States Returned to Ansible - If Query, Nothing will ever be changed.
    if succeeded:
        result['changed'] = False
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
