"""
Class for requesting authentication tokens to Keystone

This class provides means to requests for authentication tokens to be used with OpenStack's Ceilometer, Nova and RabbitMQ
"""

__authors__ = "Claudio Marques, David Palma, Luis Cordeiro"
__copyright__ = "Copyright (c) 2014 OneSource Consultoria Informatica, Lda"
__license__ = "Apache 2"
__contact__ = "www.onesource.pt"
__date__ = "01/09/2014"

__version__ = "1.0"

import urllib2
import json


class Auth:
    def __init__(self, auth_host, public_port, admin_tenant, admin_user, admin_password):

        self.auth_host = auth_host
        self.public_port = public_port
        self.admin_tenant = admin_tenant
        self.admin_user = admin_user
        self.admin_password = admin_password

    def getToken(self):
        """
        Requests and returns an authentication token to be used with OpenStack's Ceilometer, Nova and RabbitMQ
        :return: The Keystone token assigned to these credentials
        """
        auth_request = urllib2.Request("http://"+self.auth_host+":"+self.public_port+"/v2.0/tokens")
        auth_request.add_header('Content-Type', 'application/json;charset=utf8')
        auth_request.add_header('Accept', 'application/json')
        auth_data = {"auth": {"tenantName": self.admin_tenant,
                              "passwordCredentials": {"username": self.admin_user, "password": self.admin_password}}}
        auth_request.add_data(json.dumps(auth_data))
        auth_response = urllib2.urlopen(auth_request)
        response_data = json.loads(auth_response.read())
        token = response_data['access']['token']['id']
        return token