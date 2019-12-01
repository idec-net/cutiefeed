# -*- mode: python; coding: utf-8 -*-
#
# Copyright (c) 2013, 2014, 2015 Andrej Antonov <polymorphm@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

assert str is not bytes

# XXX nothing import when initialising this module! it is important!

original_create_connection = None
original_set_socket_options = None

def assert_patched():
    assert original_create_connection is not None, \
            'requests.packages.urllib3.util.connection.create_connection not patched yet'

def patched_create_connection(*args, **kwargs):
    # original function is:
    #       create_connection(
    #               address,
    #               timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
    #               source_address=None,
    #               socket_options=None,
    #               )
    
    assert_patched()
    
    from .. import socks_proxy_context
    from .. import socks_proxy
    
    socks_proxy_context_stack = socks_proxy_context.get_socks_proxy_context_stack()
    
    if not socks_proxy_context_stack:
        return original_create_connection(*args, **kwargs)
    
    socks_proxy_info = socks_proxy_context_stack[len(socks_proxy_context_stack) - 1]
    
    if socks_proxy_info is None:
        return original_create_connection(*args, **kwargs)
    
    kwargs.update(socks_proxy_info)
    
    try:
        socket_options = kwargs.pop('socket_options')
    except KeyError:
        socket_options = None
    
    sock = socks_proxy.socks_proxy_create_connection(*args, **kwargs)
    original_set_socket_options(sock, socket_options)
    
    return sock

def requests_monkey_patch():
    # XXX careful import. nothing extra!
    
    import requests.packages.urllib3.util.connection as requests_connection # or raise ImportError
    
    global original_create_connection
    global original_set_socket_options
    
    if original_create_connection is not None:
        return
    
    original_create_connection = requests_connection.create_connection # or raise AttributeError
    original_set_socket_options = requests_connection._set_socket_options # or raise AttributeError
    requests_connection.create_connection = patched_create_connection
