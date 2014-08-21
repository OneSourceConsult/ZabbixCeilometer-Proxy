
#!/usr/bin/env python
"""
Proxy for integration of resources between OpenStack's Ceilometer and Zabbix

This proxy periodically checks for changes in Ceilometer's resources reporting them to Zabbix. It is also integrated
OpenStack's Nova and RabbitMQ for reflecting changes in Projects/Tenants and Instances
"""

__authors__ = "Claudio Marques, David Palma, Luis Cordeiro"
__copyright__ = "Copyright (c) 2014 OneSource Consultoria Informatica, Lda"
__license__ = "Apache 2"
__contact__ = "www.onesource.pt"
__date__ = "01/09/2014"

__version__ = "1.0"

import threading
import project_handler
import nova_handler
import readFile
import token_handler
import zabbix_handler
import ceilometer_handler


def init_zcp(threads):
    """
        Method used to initialize the Zabbix-Ceilometer Proxy
    """

    conf_file = readFile.ReadConfFile()

    # Creation of the Auth keystone-dedicated authentication class
    # Responsible for managing AAA related requests
    keystone_auth = token_handler.Auth(conf_file.read_option('keystone_authtoken', 'keystone_host'),
                                       conf_file.read_option('keystone_authtoken', 'keystone_public_port'),
                                       conf_file.read_option('keystone_authtoken', 'admin_tenant'),
                                       conf_file.read_option('keystone_authtoken', 'admin_user'),
                                       conf_file.read_option('keystone_authtoken', 'admin_password'))

    # Creation of the Zabbix Handler class
    # Responsible for the communication with Zabbix
    zabbix_hdl = zabbix_handler.ZabbixHandler(conf_file.read_option('keystone_authtoken', 'keystone_admin_port'),
                                              conf_file.read_option('keystone_authtoken', 'nova_compute_listen_port'),
                                              conf_file.read_option('zabbix_configs', 'zabbix_admin_user'),
                                              conf_file.read_option('zabbix_configs', 'zabbix_admin_pass'),
                                              conf_file.read_option('zabbix_configs', 'zabbix_host'),
                                              conf_file.read_option('keystone_authtoken', 'keystone_host'),
                                              conf_file.read_option('zcp_configs', 'template_name'),
                                              conf_file.read_option('zcp_configs', 'zabbix_proxy_name'), keystone_auth)

    # Creation of the Ceilometer Handler class
    # Responsible for the communication with OpenStack's Ceilometer, polling for changes every N seconds
    ceilometer_hdl = ceilometer_handler.CeilometerHandler(conf_file.read_option('ceilometer_configs', 'ceilometer_api_port'),
                                                          conf_file.read_option('zcp_configs', 'polling_interval'),
                                                          conf_file.read_option('zcp_configs', 'template_name'),
                                                          conf_file.read_option('ceilometer_configs', 'ceilometer_api_host'),
                                                          conf_file.read_option('zabbix_configs', 'zabbix_host'),
                                                          conf_file.read_option('zabbix_configs', 'zabbix_port'),
                                                          conf_file.read_option('zcp_configs', 'zabbix_proxy_name'),
                                                          keystone_auth)

    #First run of the Zabbix handler for retrieving the necessary information
    zabbix_hdl.first_run()

    # Creation of the Nova Handler class
    # Responsible for detecting the creation of new instances in OpenStack, translated then to Hosts in Zabbix
    nova_hdl = nova_handler.NovaEvents(conf_file.read_option('os_rabbitmq', 'rabbit_host'),
                                            conf_file.read_option('os_rabbitmq', 'rabbit_user'),
                                            conf_file.read_option('os_rabbitmq', 'rabbit_pass'), zabbix_hdl,
                                            ceilometer_hdl)

    # Creation of the Project Handler class
    # Responsible for detecting the creation of new tenants in OpenStack, translated then to HostGroups in Zabbix
    project_hdl = project_handler.ProjectEvents(conf_file.read_option('os_rabbitmq', 'rabbit_host'),
                                                  conf_file.read_option('os_rabbitmq', 'rabbit_user'),
                                                  conf_file.read_option('os_rabbitmq', 'rabbit_pass'), zabbix_hdl)

    #Create and append threads to threads list
    th1 = threading.Thread(target=project_hdl.keystone_amq)
    threads.append(th1)

    th2 = threading.Thread(target=nova_hdl.nova_amq)
    threads.append(th2)

    th3 = threading.Thread(target=ceilometer_hdl.run())
    threads.append(th3)

    #start all the threads
    [th.start() for th in threads]


if __name__ == '__main__':
    threads = []

    init_zcp(threads)

    #wait for all threads to complete
    [th.join() for th in threads]

    print "ZCP terminated"
