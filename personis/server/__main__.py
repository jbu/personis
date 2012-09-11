#!/usr/bin/env python

from optparse import OptionParser
import logging
import os
from .server import runServer

parser = OptionParser()
parser.add_option("-m", "--models", dest="modeldir",
          help="Model directory", metavar="DIRECTORY", default='models')
parser.add_option("-c", "--config",
          dest="conf", metavar='FILE', default="server.conf",
          help="Config file")
parser.add_option("-a", "--admins",
          dest="admins", metavar='FILE',
          help="Admins file", default='admins.yaml')
parser.add_option("-o", "--oauthclients",
          dest="clients", metavar='FILE',
          help="Clients json file", default='oauth_clients.json')
parser.add_option("-t", "--tokens",
          dest="tokens", metavar='FILE',
          help="Access tokens database", default='access_tokens.dat')
parser.add_option("-l", "--log",
          dest="logging",
          help="Log level", default='INFO')
parser.add_option("-s", "--clientsecrets",
          dest="client_secrets",
          help="Client secrets file", default='client_secrets_google.json')

(options, args) = parser.parse_args()

numeric_level = getattr(logging, options.logging.upper(), None)
#cherrypy.log('Debugging%s, %d', options.logging, numeric_level)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % options.logging)
logging.basicConfig(level=numeric_level)

options.modeldir = os.path.abspath(options.modeldir)
options.conf = os.path.abspath(options.conf)
options.admins = os.path.abspath(options.admins)
options.clients = os.path.abspath(options.clients)
options.tokens = os.path.abspath(options.tokens)
options.client_secrets = os.path.abspath(options.client_secrets)

runServer(modeldir=options.modeldir, config=options.conf, admins=options.admins, clients=options.clients, tokens=options.tokens, loglevel=numeric_level, client_secrets=options.client_secrets)
