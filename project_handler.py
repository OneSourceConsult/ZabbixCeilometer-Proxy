"""
Class for Handling KeystoneEvents in OpenStack's RabbitMQ

Uses the pika library for handling the AMQP protocol, implementing the necessary callbacks for Keystone events
"""

__authors__ = "Claudio Marques, David Palma, Luis Cordeiro"
__copyright__ = "Copyright (c) 2014 OneSource Consultoria Informatica, Lda"
__license__ = "Apache 2"
__contact__ = "www.onesource.pt"
__date__ = "01/09/2014"

__version__ = "1.0"

import json
import pika


class ProjectEvents:

    def __init__(self, rabbit_host, rabbit_user, rabbit_pass, zabbix_handler):

        self.rabbit_host = rabbit_host
        self.rabbit_user = rabbit_user
        self.rabbit_pass = rabbit_pass
        self.zabbix_handler = zabbix_handler
        print 'Project Listener started'

    def keystone_amq(self):
        """
        Method used to listen to keystone events
        """

        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbit_host,
                                                                       credentials=pika.PlainCredentials(
                                                                           username=self.rabbit_user,
                                                                           password=self.rabbit_pass)))
        channel = connection.channel()
        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue
        channel.exchange_declare(exchange='keystone', type='topic')
        channel.queue_bind(exchange='openstack', queue=queue_name, routing_key='notifications.#')
        channel.queue_bind(exchange='keystone', queue=queue_name, routing_key='keystone.#')
        channel.basic_consume(self.keystone_callback, queue=queue_name, no_ack=True)
        channel.start_consuming()

    def keystone_callback(self, ch, method, properties, body):
        """
        Method used by method keystone_amq() to filter messages by type of message.

        :param ch: refers to the head of the protocol
        :param method: refers to the method used in callback
        :param properties: refers to the proprieties of the message
        :param body: refers to the message transmitted
        """
        payload = json.loads(body)

        if payload['event_type'] == 'identity.project.created':
            print "New project created - Host group created"
            tenant_id = payload['payload']['resource_info']
            tenants = self.zabbix_handler.get_tenants()
            tenant_name = self.zabbix_handler.get_tenant_name(tenants, tenant_id)

            self.zabbix_handler.group_list.append([tenant_name, tenant_id])

            self.zabbix_handler.create_host_group(tenant_name)

        elif payload['event_type'] == 'identity.project.deleted':
            print "Project deleted - Host group deleted"
            tenant_id = payload['payload']['resource_info']
            self.zabbix_handler.project_delete(tenant_id)


