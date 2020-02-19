#!/usr/bin/env python3

# Copyright: (c) 2020, World Wide Technology, All Rights Reserved
# Written By: Nick Thompson (nick.thompson@wwt.com)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

def trafficjam_base_argspec():
    return dict(host=dict(type='str', required=True),
                port=dict(type='str', required=False, default='80'),
                timeout=dict(type='int', default=10)
    )

def make_request(_method, _url, _payload, _timeout):
     # Construct the Request based on the defined method
    if _method == "get":
        _response = requests.get(_url, timeout=_timeout)
    elif _method == "post":
        _response = requests.post(_url, params=_payload, timeout=_timeout)
    elif _method == "put":
        _response = requests.put(_url, params=_payload, timeout=_timeout)
    elif _method == "delete":
        _response = requests.delete(_url, params=_payload, timeout=_timeout)
    
    # Make sure we got a valid response from the webservice
    try:
        _responsejson = _response.json()
    except ValueError:
        _responsejson = None

    # Construct a dictionary to return from the function
    _response_dict = {'response': _responsejson, 'status_code': _response.status_code}
    return _response_dict

def parse_query_return(_json_object, _key, _value):
    for _dict in _json_object:
        if _dict[_key] == _value:
            _result = True
        else:
            _result = False

    return _result

def process_response(_response):
    if 200 <= _response.get('status_code') <= 299:
        return True
    else:
        return False