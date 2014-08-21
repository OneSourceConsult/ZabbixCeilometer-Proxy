#Zabbix-Ceilometer Proxy
**A.K.A. ZCP**

##Objective
This project started as a way to integrate monitoring information collected in a Cloud environment, namely by OpenStack's Ceilometer, integrating it with an already existing monitoring solution using Zabbix.

##Features
* Integration of OpenStack's available monitoring information (e.g. using Ceilometer) with already existing Monitoring systems (e.g. Zabbix);
* Automatically gather information about the existing Cloud Infrastructure being considered (tenants, instances);
* Seamlessly handle changes in the Cloud Infrastructure (creation and deletion of tenants and/or instances);
* Periodically retrieve resources/meters details from OpenStack;
* Allow to have one common monitoring system (e.g Zabbix) for several OpenStack-based Cloud Data Centres.

##Requirements
The Zabbix-Ceilometer Proxy was written using _Python_ version 2.7.5 but can be easily ported to version 3. It uses the Pika library for support of AMQP protocol, used by OpenStack.

For installing Pika, if you already have _Python_ and the _pip_ packet manager configured, you need only to use a terminal/console and simply run:

		sudo pip install pika

If the previous command fails, download and manually install the Pika library on the host where you intend to run the ZCP:

* https://github.com/pika/pika
* http://pika.readthedocs.org/en/latest/

**Note:** Since the purpose of this project is to be integrated with OpenStack and Zabbix it is assumed that apart from a running installation of these two, some knowledge of OpenStack has already been acquired.

##Usage
Assuming that all the above requirements are met, the ZCP can be run with 3 simple steps:

1. On your OpenStack installation point to your Keystone configuration file (keystone.conf) and uncomment the following line:

		notification_driver = keystone.openstack.common.notifier.rpc_notifier

2. Edit the `proxy.conf` configuration file to reflect your own system, including the IP addresses and ports of Zabbix and of the used OpenStack modules (RabbitMQ, Ceilometer Keystone and Nova). You can also tweak some ZCP internal configurations such as the polling interval, template name and proxy name (used in Zabbix).

3. Finally, run the Zabbix-Ceilometer Proxy!

		python proxy.py

If all goes well the information retrieved from OpenStack's Ceilometer will be pushed in your Zabbix monitoring system.

**Note:** You can check out a demo from a premilinary version of ZCP running with OpenStack Havana and Zabbix [here](https://www.youtube.com/watch?v=DXz-W9fgvRk)

##Source
If not doing so already, you can check out the latest version of ZCP either through [github](https://github.com/OneSourceConsult/ZabbixCeilometer-Proxy) or [OneSource](www.onesource.pt).

##Copyright
Copyright (c) 2014 OneSource Consultoria Informatica, Lda. [🔗](http://www.onesource.pt)

This project has been developed in the scope of the MobileCloud Networking project[🔗](http://mobile-cloud-networking.eu) by Cláudio Marques, David Palma and Luis Cordeiro.

##License
Distributed under the Apache 2 license. See ``LICENSE.txt`` for more information.

##About

OneSource is the core institution that supported this work. Regarding queries about further development of custom solutions and consultancy services please contact us by email: **_geral✉️onesource.pt_** or through our website: <http://www.onesource.pt>

OneSource is a Portuguese SME specialised in the fields of data communications, security, networking and systems management, including the consultancy, auditing, design, development and lifetime administration of tailored IT solutions for corporate networks, public-sector institutions, utilities and telecommunications operators.

Our company is a start-up and technological spin-off from Instituto Pedro Nunes (IPN), a non-profit private organisation for innovation and technology transfer between the University of Coimbra and the industry and business sectors. Faithful to its origins, OneSource keeps a strong involvement in R&D activities, participating in joint research projects with academic institutions and industrial partners, in order to be able to provide its customers with state-of-art services and solutions.
