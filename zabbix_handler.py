
"""
Zabbix Handler

Provides a class responsible for the communication with Zabbix, including access to several API methods
"""

__authors__ = "Claudio Marques, David Palma, Luis Cordeiro"
__copyright__ = "Copyright (c) 2014 OneSource Consultoria Informatica, Lda"
__license__ = "Apache 2"
__contact__ = "www.onesource.pt"
__date__ = "01/09/2014"

__version__ = "1.0"

import urllib2
import json


class ZabbixHandler:
    def __init__(self, keystone_admin_port, compute_port, admin_user, zabbix_admin_pass, zabbix_host, keystone_host,
                 template_name, zabbix_proxy_name, keystone_auth):

        self.keystone_admin_port = keystone_admin_port
        self.compute_port = compute_port
        self.zabbix_admin_user = admin_user
        self.zabbix_admin_pass = zabbix_admin_pass
        self.zabbix_host = zabbix_host
        self.keystone_host = keystone_host
        self.template_name = template_name
        self.zabbix_proxy_name = zabbix_proxy_name
        self.keystone_auth = keystone_auth
        self.token = keystone_auth.getToken()

    def first_run(self):

        self.api_auth = self.get_zabbix_auth()
        self.proxy_id = self.get_proxy_id()
        self.template_id = self.get_template_id()
        tenants = self.get_tenants()
        self.group_list = []
        self.group_list = self.host_group_list(tenants)
        self.check_host_groups()
        self.check_instances()

    def get_zabbix_auth(self):
        """
        Method used to request a session ID form Zabbix API by sending Admin credentials (user, password)

        :return: returns an Id to use with zabbix api calls
        """
        payload = {"jsonrpc": "2.0",
                   "method": "user.login",
                   "params": {"user": self.zabbix_admin_user,
                              "password": self.zabbix_admin_pass},
                   "id": 2}
        response = self.contact_zabbix_server(payload)
        zabbix_auth = response['result']
        return zabbix_auth

    def create_template(self, group_id):
        """
        Method used to create a template.

        :param group_id: Receives the template group id
        :return:   returns the template id
        """
        print "Creating Template and items"
        payload = {"jsonrpc": "2.0",
                   "method": "template.create",
                   "params": {
                       "host": self.template_name,
                       "groups": {
                           "groupid": group_id
                       }
                   },
                   "auth": self.api_auth,
                   "id": 1
        }
        response = self.contact_zabbix_server(payload)
        template_id = response['result']['templateids'][0]
        self.create_items(template_id)
        return template_id

    def create_items(self, template_id):
        """
        Method used to create the items for measurements regarding the template
        :param template_id: receives the template id
        """
        items_list = ['cpu', 'cpu_util', 'disk.read.bytes', 'disk.write.bytes',
                      'disk.write.requests',
                      'disk.read.requests', 'network.incoming.bytes', 'network.incoming.packets',
                      'network.outgoing.bytes',
                      'network.outgoing.packets']
        for item in items_list:
            if item == 'cpu':
                value_type = 3
            else:
                value_type = 0
            payload = self.define_item(template_id, item, value_type)
            self.contact_zabbix_server(payload)

    def define_item(self, template_id, item, value_type):
        """
        Method used to define the items parameters

        :param template_id:
        :param item:
        :param value_type:
        :return: returns the json message to send to zabbix API
        """
        payload = {"jsonrpc": "2.0",
                   "method": "item.create",
                   "params": {
                       "name": item,
                       "key_": item,
                       "hostid": template_id,
                       "type": 2,
                       "value_type": value_type,
                       "history": "90",
                       "trends": "365",
                       "units": "",
                       "formula": "1",
                       "lifetime": "30",
                       "delay": 10
                   },
                   "auth": self.api_auth,
                   "id": 1}

        return payload

    def get_proxy_id(self):
        """
        Method used to check if the proxy exists.

        :return: a control value and the proxy ID if exists
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "proxy.get",
            "params": {
                "output": "extend"
            },
            "auth": self.api_auth,
            "id": 1
        }

        response = self.contact_zabbix_server(payload)

        proxy_id = None

        for item in response['result']:
            if item['host'] == self.zabbix_proxy_name:
                proxy_id = item['proxyid']
                break
        if not proxy_id:
            '''
            Check if proxy exists, if not create one
            '''
            payload = {"jsonrpc": "2.0",
                       "method": "proxy.create",
                       "params": {
                           "host": self.zabbix_proxy_name,
                           "status": "5"
                       },
                       "auth": self.api_auth,
                       "id": 1
            }
            response = self.contact_zabbix_server(payload)
            proxy_id = response['result']['proxyids'][0]
            return proxy_id

        return proxy_id

    def check_host_groups(self):
        """
        This method checks if some host group exists

        """
        for item in self.group_list:
            tenant_name = item[0]
            payload = {
                "jsonrpc": "2.0",
                "method": "hostgroup.exists",
                "params": {
                    "name": tenant_name
                },
                "auth": self.api_auth,
                "id": 1
            }
            response = self.contact_zabbix_server(payload)
            if response['result'] is False:
                payload = {"jsonrpc": "2.0",
                           "method": "hostgroup.create",
                           "params": {"name": tenant_name},
                           "auth": self.api_auth,
                           "id": 2}
                self.contact_zabbix_server(payload)

    def check_instances(self):
        """
        Method used to verify existence of an instance / host

        """
        servers = None
        tenant_id = None
        for item in self.group_list:
            tenant_name = item[0]
            if tenant_name == 'admin':
                tenant_id = item[1]

        auth_request = urllib2.Request(
            "http://" + self.keystone_host + ":" + self.compute_port + "/v2/" + tenant_id +
            "/servers/detail?all_tenants=1")

        auth_request.add_header('Content-Type', 'application/json;charset=utf8')
        auth_request.add_header('Accept', 'application/json')
        auth_request.add_header('X-Auth-Token', self.token)
        try:
            auth_response = urllib2.urlopen(auth_request)
            servers = json.loads(auth_response.read())

        except urllib2.HTTPError, e:
            if e.code == 401:
                print '401'
                print 'Check your keystone credentials\nToken refused!'
            elif e.code == 404:
                print 'not found'
            elif e.code == 503:
                print 'service unavailable'
            else:
                print 'unknown error: '

        for item in servers[u'servers']:
            payload = {
                "jsonrpc": "2.0",
                "method": "host.exists",
                "params": {
                    "host": item['id']
                },
                "auth": self.api_auth,
                "id": 1
            }
            response = self.contact_zabbix_server(payload)

            if response['result'] is False:
                for row in self.group_list:
                    if row[1] == item['tenant_id']:
                        instance_name = item['name']
                        instance_id = item['id']
                        tenant_name = row[0]
                        self.create_host(instance_name, instance_id, tenant_name)

    def create_host(self, instance_name, instance_id, tenant_name):

        """
        Method used to create a host in Zabbix server

        :param instance_name: refers to the instance name
        :param instance_id:   refers to the instance id
        :param tenant_name:   refers to the tenant name
        """
        group_id = self.find_group_id(tenant_name)

        if not instance_id in instance_name:
            instance_name = instance_name + '-' + instance_id

        payload = {"jsonrpc": "2.0",
                   "method": "host.create",
                   "params": {
                       "host": instance_id,
                       "name": instance_name,
                       "proxy_hostid": self.proxy_id,
                       "interfaces": [
                           {
                               "type": 1,
                               "main": 1,
                               "useip": 1,
                               "ip": "127.0.0.1",
                               "dns": "",
                               "port": "10050"}
                       ],
                       "groups": [
                           {
                               "groupid": group_id
                           }
                       ],
                       "templates": [
                           {
                               "templateid": self.template_id
                           }
                       ],

                   },
                   "auth": self.api_auth,
                   "id": 1}
        self.contact_zabbix_server(payload)

    def find_group_id(self, tenant_name):
        """
        Method used to find the the group id of an host in Zabbix server

        :param tenant_name: refers to the tenant name
        :return: returns the group id that belongs to the host_group or tenant
        """
        group_id = None
        payload = {"jsonrpc": "2.0",
                   "method": "hostgroup.get",
                   "params": {
                       "output": "extend"
                   },
                   "auth": self.api_auth,
                   "id": 2
        }
        response = self.contact_zabbix_server(payload)
        group_list = response['result']
        for line in group_list:
            if line['name'] == tenant_name:
                group_id = line['groupid']
        return group_id

    def get_template_id(self):
        """
        Method used to check if the template already exists. If not, creates one

        :return: returns the template ID
        """
        global template_id
        payload = {
            "jsonrpc": "2.0",
            "method": "template.exists",
            "params": {
                "host": self.template_name
            },
            "auth": self.api_auth,
            "id": 1
        }
        response = self.contact_zabbix_server(payload)

        if response['result'] is True:

            payload = {"jsonrpc": "2.0",
                       "method": "template.get",
                       "params": {
                           "output": "extend",
                           "filter": {
                               "host": [
                                   self.template_name
                               ]
                           }
                       },
                       "auth": self.api_auth,
                       "id": 1
            }
            response = self.contact_zabbix_server(payload)
            global template_id
            for item in response['result']:
                template_id = item['templateid']
        else:
            group_id = self.get_group_template_id()
            template_id = self.create_template(group_id)
        return template_id

    def get_group_template_id(self):
        """
        Method used to get the the group template id. Used to associate a template to the templates group.

        :return: returns the template group id
        """
        group_template_id = None
        payload = {"jsonrpc": "2.0",
                   "method": "hostgroup.get",
                   "params": {
                       "output": "extend",
                       "filter": {
                           "name": [
                               "Templates"
                           ]
                       }
                   },
                   "auth": self.api_auth,
                   "id": 1
        }
        response = self.contact_zabbix_server(payload)

        for item in response['result']:
            group_template_id = item['groupid']
        return group_template_id

    def find_host_id(self, host):
        """
        Method used to find a host Id in Zabbix server

        :param host:
        :return: returns the host id
        """
        host_id = None
        payload = {"jsonrpc": "2.0",
                   "method": "host.get",
                   "params": {
                       "output": "extend"
                   },
                   "auth": self.api_auth,
                   "id": 2
        }
        response = self.contact_zabbix_server(payload)
        hosts_list = response['result']
        for line in hosts_list:
            if host == line['host']:
                host_id = line['hostid']
        return host_id

    def delete_host(self, host_id):
        """
        Method used to delete a Host in Zabbix Server

        :param host_id: refers to the host id to delete
        """
        payload = {"jsonrpc": "2.0",
                   "method": "host.delete",
                   "params": [
                       host_id
                   ],
                   "auth": self.api_auth,
                   "id": 1
        }
        self.contact_zabbix_server(payload)

    def get_tenants(self):
        """
        Method used to get a list of tenants from keystone

        :return: list of tenants
        """
        tenants = None
        auth_request = urllib2.Request('http://' + self.keystone_host + ':'+self.keystone_admin_port+'/v2.0/tenants')
        auth_request.add_header('Content-Type', 'application/json;charset=utf8')
        auth_request.add_header('Accept', 'application/json')
        auth_request.add_header('X-Auth-Token', self.token)

        try:
            auth_response = urllib2.urlopen(auth_request)
            tenants = json.loads(auth_response.read())
        except urllib2.HTTPError, e:
            if e.code == 401:
                print '401'
                print 'Check your keystone credentials\nToken refused!'
            elif e.code == 404:
                print 'not found'
            elif e.code == 503:
                print 'service unavailable'
            else:
                print 'unknown error: '
        return tenants

    def get_tenant_name(self, tenants, tenant_id):
        """
        Method used to get a name of a tenant using its id

        :param tenants: refers to an array of tenants
        :param tenant_id: refers to a tenant id
        :return: returns a tenant name
        """
        for item in tenants['tenants']:
            if item['id'] == tenant_id:
                global tenant_name
                tenant_name = item['name']
        return tenant_name

    def host_group_list(self, tenants):
        """
        Method to "fill" an array of hosts

        :param tenants: receive an array of tenants
        :return: parsed list of hosts [[tenant_name1, uuid1], [tenant_name2, uuid2], ..., [tenant_nameN, uuidN],]
        """
        host_group_list = []
        for item in tenants['tenants']:
            if not item['name'] == 'service':
                host_group_list.append([item['name'], item['id']])

        return host_group_list

    def project_delete(self, tenant_id):
        """
        Method used to delete a project

        :param tenant_id: receives a tenant id
        """

        for item in self.group_list:
            if item[1] == tenant_id:
                tenant_name = item[0]
                group_id = self.find_group_id(tenant_name)
                self.delete_host_group(group_id)
                self.group_list.remove(item)

    def delete_host_group(self, group_id):
        """
        Thos method deletes a host group
        :param group_id: receives the group id
        """
        payload = {"jsonrpc": "2.0",
                   "method": "hostgroup.delete",
                   "params": [group_id
                   ],
                   "auth": self.api_auth,
                   "id": 1
        }
        self.contact_zabbix_server(payload)

    def create_host_group(self, tenant_name):
        """
        This method is used to create host_groups. Every tenant is a host group

        :param tenant_name: receives teh tenant name
        """
        payload = {"jsonrpc": "2.0",
                   "method": "hostgroup.create",
                   "params": {"name": tenant_name},
                   "auth": self.api_auth,
                   "id": 2}
        self.contact_zabbix_server(payload)

    def contact_zabbix_server(self, payload):
        """
        Method used to contact the Zabbix server.

        :param payload: refers to the json message to send to Zabbix
        :return: returns the response from the Zabbix API
        """
        data = json.dumps(payload)
        req = urllib2.Request('http://'+self.zabbix_host+'/zabbix/api_jsonrpc.php', data,
                              {'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        response = json.loads(f.read())
        f.close()
        return response