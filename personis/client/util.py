#!/usr/bin/env python


# The Personis system is copyright 2000-2012 University of Sydney
#       Bob.Kummerfeld@Sydney.edu.au

# This file is part of Personis.

# Personis is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Personis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Personis.  If not, see <http://www.gnu.org/licenses/>.

#
# Active User Models: added subscribe method to Access
#

import os, traceback
import json
#from django.utils import simplejson as json
import string
import httplib2
import pickle
import types
import time
import logging
import personis.client

from oauth2client.file import Storage
from oauth2client.client import Credentials, OAuth2WebServerFlow, flow_from_clientsecrets
from oauth2client.tools import run
import httplib2

def do_call(fun, args, connection):
    """

    :param fun:
    :param args:
    :param connection:
    :return:
    :raise:
    """
    if (not connection.valid()):
        raise SystemError('Need http or modelserver and credentials')
    args["version"] = "11.2"
    args_json = json.dumps(args)+'\n'

    http = connection.get_http()
    uri = connection.uri + fun
    logging.info('do_call uri: %s, body: %s', uri, args_json)
    try:
        resp, content = http.request(uri, method="POST", headers={'Content-Type': 'application/json'}, body=args_json)
        logging.info('Resp: %s, content: %s',resp, content)
    except Exception as e:
        logging.info('httperror: %s',e )
        raise e
    try:
        result = json.loads(content)
    except:
        logging.info( "json loads failed!")
        logging.info( "<<%s>>" % (content))
        raise ValueError, "json loads failed"
    # dirty kludge to get around unicode
    for k,v in result.items():
        if type(v) == type(u''):
            result[k] = str(v)
        if type(k) == type(u''):
            del result[k]
            result[str(k)] = v
    ## Unpack the error, and if it is an exception throw it.
    if type(result) == types.DictionaryType and "result" in result:
        if result["result"] == "error":
            logging.info( result)
            # We have returned with an error, so throw it as an exception.
            if "pythonPickel" in result:
                raise pickle.loads(result["pythonPickel"])
            elif len(result["val"]) == 3:
                print str(result["val"][2])
                raise pickle.loads(str(result["val"][2]))
            else:
                raise Exception, str(result["val"])
        else:
            # Unwrap the result, and return as normal. 
            result = result["val"]
        return result

def MkModel( model=None, modelserver=None, user=None, password=None, description=None, debug=0):
    """

    :param model:
    :param modelserver:
    :param user:
    :param password:
    :param description:
    :param debug:
    :raise:
    """
    if modelserver == None:
        raise ValueError, "modelserver is None"
    if ':' in modelserver:
        modelserver, modelport = modelserver.split(":")
    else:
        modelport = 2005 # default port for personis server
    modelname = model
    ok = False
    try:
        ok = do_call(modelserver, modelport, "mkmodel", {'modelname':modelname,\
                                                                'descripion':description,\
                                                                'user':user,\
                                                                'password':password})
    except:
        logging.info(traceback.format_exc())
        raise ValueError, "cannot create model '%s', server '%s'" % (modelname, modelserver)
    if not ok:
        raise ValueError, "server '%s' cannot create model '%s'" % (modelserver, modelname)

# utility function to display an object
def showobj(obj, indent):
    """

    :param obj:
    :param indent:
    """
    print "showobj:"
    for k,v in obj.__dict__.items():
        if ((k == 'time') or (k == 'creation_time')) and (v != None):
            print "%*s %s %s %s (%s)" % (indent, " ", k,"=",time.ctime(v),v)
        elif k == "evidencelist":
            print "%*s %s %s %d items" % (indent, " ", k,"=",len(v))
        else:
            print "%*s %s %s %s" % (indent, " ", k,"=",v)


# utility to print a list of component objects + evidence if printev="yes"
def PrintComplist(reslist, printev=None, count=1):
    """

    :param reslist:
    :param printev:
    :param count:
    """
    print "count =", count
    for res in reslist:
        print "==================================================================="
        print "Component: ", res.Description
        print "==================================================================="
        showobj(res, 0)
        if res.value_type == "JSON":
            jval = json.loads(res.value)
            print "Value:",jval
        if printev == "yes":
            print "---------------------------------"
            print "Evidence about it"
            print "---------------------------------"
            if res.evidencelist is None:
                print "no evidence"
            else:
                evlist = res.evidencelist
                evlist.reverse()
                for ev in evlist[:count]:
                    if type(ev) == type(dict()):
                        showobj(Struct(**ev), 10)
                    else:
                        showobj(ev, 10)
                    print "---------------------------------"

class Struct:
    def __init__(self, **entries): 
        self.__dict__.update(entries)


def getOauthCredentialsFromClientSecrets(credentials='credentials.dat', filename = 'client_secrets.json', http=None):

    # If the Credentials don't exist or are invalid run through the native client
    # flow. The Storage object will ensure that if successful the good
    # Credentials will get written back to a file.

    """

    :param credentials:
    :param filename:
    :param http:
    :return:
    """
    storage = Storage(credentials)
    credentials = storage.get()
    FLOW = flow_from_clientsecrets(filename, scope='https://www.personis.com/auth/model')
    if credentials is None or credentials.invalid:
        credentials = run(FLOW, storage, http)
    personis_uri = json.loads(open(filename,'r').read())['installed']['token_uri'][:-len('request_token')]
    return credentials, personis_uri

def LoginFromClientSecrets(filename = 'client_secrets.json', credentials = 'credentials.dat', http=None):
    """

    :param filename:
    :param credentials:
    :param http:
    :return:
    """
    cred, personis_uri = getOauthCredentialsFromClientSecrets(filename = filename, credentials = credentials, http = http)
    return personis.client.Access(uri = personis_uri, credentials = cred, http=http)