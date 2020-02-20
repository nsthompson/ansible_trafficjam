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
module: trafficjam_vrfs

short_description: This module is used to create, delete, and query information about VRFs in the WWT ATC Tool TrafficJam

version_added: "2.9"

description:
    - "This module is used to create, delete, and query information about VRFs in the WWT ATC Tool TrafficJam"

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
    vrf_name:
        description:
            - Name of the VRF to be created
        required: false
    vrf_id:
        description:
            - ID (integer) of the existing VRF
        required: false
    vrf_table_id:
        description:
            - ID (integer) of the Routing Table bound to the new VRF.  Used when creating a VRF.
        required: false
    interface_id:
        description:
            - ID (integer) of the interface to bind to the VRF.
    state:
        description:
            - Parameter to determine module behavior.  Can be query / present / absent.  Default is query.
        required: false

author:
    - Nick Thompson (nick.thompson@wwt.com)
'''

EXAMPLES = '''
# Get Information for all VRFs
- name: Get VRF Information
  trafficjam_vrfs:
    host: trafficjam
    state: query

# Get Information for specific VRF
- name: Get Specific VRF Information
  trafficjam_vrfs:
    host: trafficjam
    vrf_id: 10
    state: query

# Create VRF
- name: Create VRF
  trafficjam_vrfs:
    host: trafficjam
    vrf_name: testvrf
    vrf_table_id: 111
    state: present

# Bind VRF to an interface
- name: Bind VRF to Interface
  trafficjam_vrfs:
    host: trafficjam
    vrf_id: 10
    interface_id: 100
    state: present

# Delete VRF
- name: Delete VRF
  trafficjam_vrfs:
    host: trafficjam
    vrf_id: 10
    state: absent
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
from ansible_collections.wwt.trafficjam.plugins.module_utils.trafficjam import (
    trafficjam_base_argspec,
    make_request,
    parse_query_return,
    process_response
)


def generate_url(_params):
    # Gather Parameters
    _state = _params['state']
    _host = _params['host']
    _port = _params['port']

    # Default _payload to None.  If required, this will be set below.
    _payload = None

    # Generate URL for Query Requests
    if _state == "query" and not _params['vrf_id']:
        _url = f"http://{_host}:{_port}/trafficjam/api/vrfs"
        _http_method = "get"

        # Construct a dictionary to return results with
        _response_dict = {"url": _url, "http_method": _http_method, "data": _payload}
        return _response_dict

    elif _state == "query" and _params.get('vrf_id'):
        _url = f"http://{_host}:{_port}/trafficjam/api/vrfs/{_params['vrf_id']}"
        _http_method = "get"

        # Construct a dictionary to return results with
        _response_dict = {"url": _url, "http_method": _http_method, "data": _payload}
        return _response_dict

    # Generate URL for Present Requests.
    # HTTP Method of POST is used for creating new VRFs.
    # PUT is used for binding a VRF to an interface.
    if _state == "present" and _params['vrf_name'] and _params['vrf_table_id']:
        _url = f"http://{_host}:{_port}/trafficjam/api/vrfs"
        _http_method = "post"
        _payload = {"name": _params['vrf_name'], "table": _params['vrf_table_id']}

        # Construct a dictionary to return results with
        _response_dict = {"url": _url, "http_method": _http_method, "data": _payload}
        return _response_dict

    elif _state == "present" and _params['vrf_id'] and _params['interface_id']:
        _url = f"http://{_host}:{_port}/trafficjam/api/vrfs/{_params['vrf_id']}"
        _http_method = "put"
        _payload = {"interface_id": _params['interface_id']}

        # Construct a dictionary to return results with
        _response_dict = {"url": _url, "http_method": _http_method, "data": _payload}
        return _response_dict

    # Generate URL for Absent Requests
    if _state == "absent" and _params['vrf_id']:
        _url = f"http://{_host}:{_port}/trafficjam/api/vrfs/{_params['vrf_id']}"
        _http_method = "delete"

        # Construct a dictionary to return results with
        _response_dict = {"url": _url, "http_method": _http_method, "data": _payload}
        return _response_dict


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = trafficjam_base_argspec()
    module_args.update(
        vrf_name=dict(type='str', required=False),
        vrf_id=dict(type='int', required=False),
        vrf_table_id=dict(type='int', required=False),
        interface_id=dict(type='int', required=False),
        state=dict(type='str', choices=['query', 'present', 'absent'], default='query')
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
        mutually_exclusive=[
            ['vrf_name', 'interface_id'],
            ['vrf_table_id', 'interface_id']
        ],
        required_by=dict(
            vrf_name=['vrf_table_id'],
            vrf_table_id=['vrf_name']
        ),
        required_if=[
            ['state', 'present', ['vrf_name', 'vrf_table_id', 'vrf_id', 'vrf_table_id'], True],
            ['state', 'absent', ['vrf_id']]
        ]
    )

    # Collect Module Parameters
    host = module.params['host']
    port = module.params['port']

    # Generate the URL, HTTP Method, and Optional Payload based on Module Parameters
    url_response = generate_url(module.params)

    url = url_response['url']
    http_method = url_response['http_method']
    payload = url_response['data']

    # We need to validate if the VRF exists already before adding it
    if http_method == "post":
        query_url = f"http://{host}:{port}/trafficjam/api/vrfs"
        query_method = "get"
        query_response = make_request(query_method, query_url, payload, module.params['timeout'])

        if parse_query_return(query_response['response'], 'name', module.params['vrf_name']):
            result['response'] = query_response['response']
            result['status_code'] = query_response['status_code']
            module.fail_json(msg='vrf already exists', **result)

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
