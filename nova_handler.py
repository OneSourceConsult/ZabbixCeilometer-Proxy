"""
Class for Handling Nova events in OpenStack's RabbitMQ

Uses the pika library for handling the AMQP protocol, implementing the necessary callbacks for Nova events
"""

__authors__ = "Claudio Marques, David Palma, Luis Cordeiro"
__copyright__ = "Copyright (c) 2014 OneSource Consultoria Informatica, Lda"
__license__ = "Apache 2"
__contact__ = "www.onesource.pt"
__date__ = "01/09/2014"

__version__ = "1.0"

import json
import pika


class NovaEvents:

    def __init__(self, rabbit_host, rabbit_user, rabbit_pass, zabbix_handler, ceilometer_handler):

        """
        TODO
        :type self: object
        """
        self.rabbit_host = rabbit_host
        self.rabbit_user = rabbit_user
        self.rabbit_pass = rabbit_pass
        self.zabbix_handler = zabbix_handler
        self.ceilometer_handler = ceilometer_handler
        print 'Nova listener started'

    def nova_amq(self):
        """
        Method used to listen to nova events

        """

        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.rabbit_host,
                                                                       credentials=pika.PlainCredentials(
                                                                           username=self.rabbit_user,
                                                                           password=self.rabbit_pass)))
        channel = connection.channel()
        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue
        channel.exchange_declare(exchange='nova', type='topic')
        channel.queue_bind(exchange='nova', queue=queue_name, routing_key='notifications.#')
        channel.queue_bind(exchange='nova', queue=queue_name, routing_key='compute.#')
        channel.basic_consume(self.nova_callback, queue=queue_name, no_ack=True)
        channel.start_consuming()

    def nova_callback(self, ch, method, properties, body):
        """
        Method used by method nova_amq() to filter messages by type of message.

        :param ch: refers to the head of the protocol
        :param method: refers to the method used in callback
        :param properties: refers to the proprieties of the message
        :param body: refers to the message transmitted
        """
        payload = json.loads(body)

        try:

            tenant_name = payload['_context_project_name']
            type_of_message = payload['event_type']

            if type_of_message == 'compute.instance.create.end':
                instance_id = payload['payload']['instance_id']
                instance_name = payload['payload']['hostname']
                self.zabbix_handler.create_host(instance_name, instance_id, tenant_name)
                print "Creating a host in Zabbix Server"
                self.ceilometer_handler.host_list = self.ceilometer_handler.get_hosts_ID()

            elif type_of_message == 'compute.instance.delete.end':
                host = payload['payload']['instance_id']
                try:
                    host_id = self.zabbix_handler.find_host_id(host)
                    self.zabbix_handler.delete_host(host_id)
                    print "Deleting host from Zabbix Server"
                    self.ceilometer_handler.host_list = self.ceilometer_handler.get_hosts_ID()

                except:
                    pass    # TODO
            else:
                pass    # TODO
        except:
            pass    # TODO
