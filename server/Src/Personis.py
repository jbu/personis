#!/usr/bin/env python

#
# The Personis system is copyright 2000-2011 University of Sydney
# Licenced under GPL v3
#


import sys
import cherrypy
import Personis_server
import Personis_base
from Personis_exceptions import *
import socket
import os
import argparse
from optparse import OptionParser
from multiprocessing import Process, Queue
import cronserver
import oauth2client

class Access(Personis_server.Access):

	def __init__(self, connection = None, debug=0):

		Personis_server.Access.__init__(self, connection = connection, debug=debug)


class CliAccess(Personis_server.Access):

	def __init__(self, model = None, user=None, password=None, configfile="~/.personis.conf", modelserver=None, debug=0):
		self.model = model
		self.debug = debug
		self.port = 2005
		self.hostname = 'localhost'
		self.modelname = model
		self.configfile = configfile
		self.configfile = os.path.expanduser(configfile)

		self.config = ConfigParser.ConfigParser()
		
		try: 
			self.config.readfp(open(self.configfile, "r"), self.configfile)
			self.port = self.config.get('personis_client', 'client.serverPort')
		except: 
			pass

		try: 
			self.hostname = self.config.get('personis_client','client.serverHost')
			# hack to cope with different config parsers used by cherrypy and standard python
			if self.hostname[:1] in ['"',"'"] and  self.hostname[-1:] in ['"',"'"]:
				self.hostname = self.hostname[1:-1] # strip off quotes
		except: 
			pass
		try:
			(self.modelname, modelserver) = self.modelname.split('@')
		except:
			pass
		if modelserver == None:
			self.modelserver = self.hostname + ":" + str(self.port)
		else:
			self.modelserver = modelserver
		#print self.modelname, self.modelserver

		Personis_server.Access.__init__(self, model=self.modelname, modelserver=self.modelserver, user=user, password=password, debug=debug)



if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-m", "--models", dest="models",
              help="Model directory", metavar="DIRECTORY", default='models')
    parser.add_option("-c", "--config",
              dest="config", metavar='FILE',
              help="Config file")
    parser.add_option("-a", "--admins",
              dest="admins", metavar='FILE',
              help="Admins file", default='admins.yaml')
    parser.add_option("-o", "--oauthconfig",
              dest="oauth", metavar='FILE',
              help="Oauth config file", default='oauth.yaml')
    parser.add_option("-l", "--log",
              dest="log", metavar='FILE',
              help="Log file", default='stdout')

    (options, args) = parser.parse_args()

    if options.log != "stdout":
		sys.stdout = open(options.log, "w", 0)

    Personis_server.runServer(options.models, options.config, options.admins, options.oauth)

