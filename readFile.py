"""
Class for reading the configuration file

Uses the ConfigParser lib to return the values present in the config file
"""

__authors__ = "Claudio Marques, David Palma, Luis Cordeiro"
__copyright__ = "Copyright (c) 2014 OneSource Consultoria Informatica, Lda"
__license__ = "Apache 2"
__contact__ = "www.onesource.pt"
__date__ = "01/09/2014"

__version__ = "1.0"

import ConfigParser


class ReadConfFile:

    config = None

    def __init__(self, file="proxy.conf"):

        """
        Method to read from conf file specific options

        :param file:
        """
        self.config = ConfigParser.SafeConfigParser()
        self.config.readfp(open(file))

    def read_option(self, group, name):
        """
        :return:
        """
        value = self.config.get(group, name)
        return value