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
module: trafficjam_physical_interfaces

short_description: This module is used to create, delete, and query information about physical Interfaces in the WWT ATC Tool TrafficJam

version_added: "2.9"

description:
    - "This module is used to create, delete, and query information about physical Interfaces in the WWT ATC Tool TrafficJam"

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
    subinterface:
        description:
            - Enable Subinterface mode
        required: false
        default: false
        choices:
            - true
            - false
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

    name:
        description:
            - Interface Name
        required: false
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
            - ID (integer) of an existing VRF
        required: false
    physical_id:
        description:
            - ID (integer) of an existing physical interface
        required: false
    subinterface_id:
        description:
            - ID (integer) of the subinterface
        required: false
    bridge_id:
        description:
            - ID (integer) of an existing bridge interface
    vlan_id:
        description:
            - ID (integer) of the provisioned VLAN
        required: false
    mtu:
        description:
            - Maximum Transmission Unit (integer) setting of the physical interface
        required: false

author:
    - Nick Thompson (nick.thompson@wwt.com)
'''

EXAMPLES = '''
# Get Information for all Physical Interfaces
- name: Get Physical Interface Information
  trafficjam_physical_interfaces:
    host: trafficjam
    state: query

# Get Information for specific Physical Interface
- name: Get Specific Physical Interface Information
  trafficjam_physical_interfaces:
    host: trafficjam
    state: query
    config:
        physical_id: 3

# Get Information for all Physical Subinterfaces
- name: Get Physical Subinterface Information
  trafficjam_physical_interfaces:
    host: trafficjam
    subinterface: true
    state: query
    config:
        physical_id: 3

# Get Information for a specific Physical Subinterface
- name: Get Specific Physical Subinterface Information
  trafficjam_physical_interfaces:
    host: trafficjam
    subinterface: true
    state: query
    config:
        physical_id: 3
        subinterface_id: 39

# Update Existing Physical Interface Configuration
- name: Update Existing Physical Interface Configuration
  trafficjam_physical_interfaces:
    host: trafficjam
    state: present
    config:
      description: "Interface Connected to Router1"
      v4_address: 1.1.1.1/24
      physical_id: 3

# Create New Subinterface
- name: Create New Subinterface
  trafficjam_physical_interfaces:
    host: trafficjam
    subinterface: true
    state: present
    config:
      description: "New Subinterface"
      v4_address: 2.2.2.2/24
      physical_id: 3
      vlan_id: 222

# Update Existing Subinterface
- name: Update Existing Subinterface
  trafficjam_physical_interfaces:
    host: trafficjam
    subinterface: true
    state: present
    config:
      description: "Updated Subinterface"
      physical_id: 3
      subinterface_id: 39
      v4_address: 3.3.3.3/24

# Delete Existing Subinterface
- name: Delete Existing Subinterface
  trafficjam_physical_interfaces:
    host: trafficjam
    subinterface: true
    state: absent
    config:
      physical_id: 3
      subinterface_id: 39

# Delete Existing Physical Interface Configuration
- name: Delete Existing Physical Interface Configuration
  trafficjam_physical_interfaces:
    host: trafficjam
    state: absent
    config:
      physical_id: 3
      description: "Interface Connected to Router1"
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
from ansible_collections.wwt.trafficjam.plugins.module_utils.trafficjam import (
    trafficjam_base_argspec,
    make_request,
    parse_query_return,
    process_response
)


def scrub_params(_params):
    #
    # The builtin methods for scrubbing parameters do not handle nested dictionaries,
    # so we have to do it here
    #

    # Some parameters are mutually exclusive
    if _params['config'] is not None and _params['config']['subinterface_id'] is not None and _params['config']['vlan_id'] is not None:
        _errormsg = "parameter subinterface_id is mutually exclusive with vlan_id"
        return _errormsg

    # Some parameters have dependencies
    if not _params['subinterface']:
        if _params['state'] == "present":
            if (_params['config'] is not None and _params['config']['physical_id'] is None):
                _errormsg = "missing parameter(s) required: physical_id"
                return _errormsg

    if _params['subinterface']:
        if _params['state'] == "query":
            if (_params['subinterface'] and _params['config'] is None) or (_params['subinterface'] and _params['config']['physical_id'] is None):
                _errormsg = "missing parameter(s) required by 'subinterface': physical_id"
                return _errormsg

        if _params['state'] == "present":
            if (_params['subinterface'] and _params['config'] is None):
                _errormsg = "missing parameter(s) required by 'subinterface': physical_id|vlan_id or physical_id|subinterface_id"
                return _errormsg
            elif (_params['subinterface'] and _params['config']['physical_id'] and _params['config']['vlan_id'] and _params['config']['subinterface_id'] is None):
                _errormsg = None
                return _errormsg
            elif (_params['subinterface'] and _params['config']['physical_id'] and _params['config']['subinterface_id'] and _params['config']['vlan_id'] is None):
                _errormsg = None
                return _errormsg
            else:
                _errormsg = "missing parameter(s) required by 'subinterface': physical_id|vlan_id or physical_id|subinterface_id"
                return _errormsg


def generate_url(_params):
    # Gather Parameters
    _host = _params['host']
    _port = _params['port']

    # Default _payload to None.  If required, this will be set below.
    _payload = None

    # Generate URL for Query Requests
    if _params['state'] == "query":
        # Generate URLs for non-subinterface requests
        if (not _params['subinterface'] and _params['config'] is None) or (not _params['subinterface'] and _params['config']['physical_id'] is None):
            _url = f"http://{_host}:{_port}/trafficjam/api/interfaces/physicals"
            _http_method = "get"

            # Construct a dictionary to return results with
            _response_dict = {"url": _url, "http_method": _http_method, "data": _payload}
            return _response_dict

        elif not _params['subinterface'] and _params['config']['physical_id']:
            _url = f"http://{_host}:{_port}/trafficjam/api/interfaces/physicals/{_params['config']['physical_id']}"
            _http_method = "get"

            # Construct a dictionary to return results with
            _response_dict = {"url": _url, "http_method": _http_method, "data": _payload}
            return _response_dict

        # Generate URLs for subinterface requests
        if _params['subinterface'] and _params['config']['physical_id'] and _params['config']['subinterface_id'] is None:
            _url = f"http://{_host}:{_port}/trafficjam/api/interfaces/physicals/{_params['config']['physical_id']}/subinterfaces"
            _http_method = "get"

            # Construct a dictionary to return results with
            _response_dict = {"url": _url, "http_method": _http_method, "data": _payload}
            return _response_dict

        if _params['subinterface'] and _params['config']['physical_id'] and _params['config']['subinterface_id']:
            _url = f"http://{_host}:{_port}/trafficjam/api/interfaces/physicals/{_params['config']['physical_id']}/subinterfaces/{_params['config']['subinterface_id']}"
            _http_method = "get"

            # Construct a dictionary to return results with
            _response_dict = {"url": _url, "http_method": _http_method, "data": _payload}
            return _response_dict

    # Generate URL for Present Requests
    if _params['state'] == "present":
        # Generate URLs for non-subinterface requests.
        # All of these use the PUT method as we update an existing physical interface.
        if not _params['subinterface'] and _params['config']['physical_id'] is not None:
            _url = f"http://{_host}:{_port}/trafficjam/api/interfaces/physicals/{_params['config']['physical_id']}"
            _http_method = "put"
            _payload = {
                "description": _params['config']['description'],
                "v4_address": _params['config']['v4_address'],
                "v6_address": _params['config']['v6_address'],
                "vrf_id": _params['config']['vrf_id'],
                "bridge_id": _params['config']['bridge_id'],
                "mtu": _params['config']['mtu']
                }

            # Construct a dictionary to return results with
            _response_dict = {"url": _url, "http_method": _http_method, "data": _payload}
            return _response_dict

        # Generate URLs for subinterface requests
        if _params['subinterface'] and _params['config']['physical_id'] is not None and _params['config']['vlan_id'] is not None:
            _url = f"http://{_host}:{_port}/trafficjam/api/interfaces/physicals/{_params['config']['physical_id']}/subinterfaces"
            _http_method = "post"
            _payload = {
                "description": _params['config']['description'],
                "v4_address": _params['config']['v4_address'],
                "v6_address": _params['config']['v6_address'],
                "vrf_id": _params['config']['vrf_id'],
                "bridge_id": _params['config']['bridge_id'],
                "vlan_id": _params['config']['vlan_id']
                }

            # Construct a dictionary to return results with
            _response_dict = {"url": _url, "http_method": _http_method, "data": _payload}
            return _response_dict

        if _params['subinterface'] and _params['config']['physical_id'] is not None and _params['config']['subinterface_id'] is not None:
            _url = f"http://{_host}:{_port}/trafficjam/api/interfaces/physicals/{_params['config']['physical_id']}/subinterfaces/{_params['config']['subinterface_id']}"
            _http_method = "put"
            _payload = {
                "description": _params['config']['description'],
                "v4_address": _params['config']['v4_address'],
                "v6_address": _params['config']['v6_address'],
                "vrf_id": _params['config']['vrf_id'],
                "bridge_id": _params['config']['bridge_id']
                }

            # Construct a dictionary to return results with
            _response_dict = {"url": _url, "http_method": _http_method, "data": _payload}
            return _response_dict

    # Generate URL for Absent Requests
    if _params['state'] == "absent":
        if not _params['subinterface'] and _params['config']['physical_id'] is not None:
            _url = f"http://{_host}:{_port}/trafficjam/api/interfaces/physicals/{_params['config']['physical_id']}"
            _http_method = "delete"
            _payload = {
                "description": _params['config']['description'],
                "v4_address": _params['config']['v4_address'],
                "v6_address": _params['config']['v6_address'],
                "vrf_id": _params['config']['vrf_id'],
                "bridge_id": _params['config']['bridge_id'],
                "mtu": _params['config']['mtu']
                }

            # Construct a dictionary to return results with
            _response_dict = {"url": _url, "http_method": _http_method, "data": _payload}
            return _response_dict

        if _params['subinterface'] and _params['config']['physical_id'] is not None and _params['config']['subinterface_id'] is not None:
            _url = f"http://{_host}:{_port}/trafficjam/api/interfaces/physicals/{_params['config']['physical_id']}/subinterfaces/{_params['config']['subinterface_id']}"
            _http_method = "delete"

            # Construct a dictionary to return results with
            _response_dict = {"url": _url, "http_method": _http_method, "data": _payload}
            return _response_dict


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = trafficjam_base_argspec()

    config_spec = dict(
        description=dict(type='str', required=False),
        v4_address=dict(type='str', required=False),
        v6_address=dict(type='str', required=False),
        vrf_id=dict(type='int', required=False),
        physical_id=dict(type='int', required=False),
        subinterface_id=dict(type='int', required=False),
        bridge_id=dict(type='int', required=False),
        vlan_id=dict(type='int', required=False),
        mtu=dict(type='int', required=False)
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

    # Collect Module Parameters
    host = module.params['host']
    port = module.params['port']
    timeout = module.params['timeout']
    subinterface = module.params['subinterface']

    if module.params['config'] is not None and module.params['config']['physical_id'] is not None:
        physical_id = module.params['config']['physical_id']
    else:
        physical_id = None

    # Run through some error checking and scrub the received parameters
    errormsg = scrub_params(module.params)

    if errormsg is not None:
        result['changed'] = True
        result['failed'] = False
        module.fail_json(msg=errormsg, **result)

    # Generate the URL and HTTP Method based on Module Parameters
    url_response = generate_url(module.params)

    url = url_response['url']
    http_method = url_response['http_method']
    payload = url_response['data']

    # We need to validate if the interface exists already before adding it
    if http_method == "post":
        # Generate URL for Non-Subinterface Requests
        if subinterface and physical_id is not None:
            query_url = f"http://{host}:{port}/trafficjam/api/interfaces/physicals/{physical_id}/subinterfaces"
            query_method = "get"

        # Make the request
        query_response = make_request(query_method, query_url, payload, timeout)

        if query_response['response']:
            if subinterface and physical_id is not None:
                if parse_query_return(query_response['response'], 'vlan_id', module.params['config']['vlan_id']):
                    result['response'] = query_response['response']
                    result['status_code'] = query_response['status_code']
                    module.fail_json(msg='physical subinterface already exists', **result)

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
