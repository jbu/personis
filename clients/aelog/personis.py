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

def do_call(fun, args, connection):
    if (not connection.valid()):
        raise SystemError('Need http or modelserver and credentials')
    args["version"] = "11.2"
    args_json = json.dumps(args)+'\n'

    http = connection.get_http()
    resp, content = http.request(connection.uri+fun, method="POST", headers={'Content-Type': 'application/json'}, body=args_json)

    try:
        result = json.loads(content)
    except:
        print "json loads failed!"
        print "<<%s>>" % (content)
        raise ValueError, "json loads failed"
    # dirty kludge to get around unicode
    for k,v in result.items():
        if type(v) == type(u''):
            result[k] = str(v)
        if type(k) == type(u''):
            del result[k]
            result[str(k)] = v
    ## Unpack the error, and if it is an exception throw it.
    if type(result) == types.DictionaryType and result.has_key("result"):
        if result["result"] == "error":
            print result
            # We have returned with an error, so throw it as an exception.
            if result.has_key("pythonPickel"):
                raise pickle.loads(result["pythonPickel"])
            elif len(result["val"]) == 3:
                raise pickle.loads(str(result["val"][2]))
            else:
                raise Exception, str(result["val"])
        else:
            # Unwrap the result, and return as normal. 
            result = result["val"]
        return result

class Connection(object):

    def __init__(self, uri = None, credentials = None, http = None):
        self.http = http
        self.credentials = credentials
        self.uri = uri
        self.authorized = False

    def valid(self):
        if self.uri == None or self.credentials == None:
            return False
        return True

    def get_http(self):
        if self.http == None:
            self.http = httplib2.Http()
        if not self.authorized:
            self.credentials.authorize(self.http)
            self.authorized = True
        return self.http

def MkModel( model=None, modelserver=None, user=None, password=None, description=None, debug=0):
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
        if debug >0:
            traceback.print_exc()
        raise ValueError, "cannot create model '%s', server '%s'" % (modelname, modelserver)
    if not ok:
        raise ValueError, "server '%s' cannot create model '%s'" % (modelserver, modelname)

ComponentTypes = ["attribute", "activity", "knowledge", "belief", "preference", "goal"]
ValueTypes = ["string", "number", "boolean", "enum", "JSON"]
EvidenceTypes = ["explicit", # given by the user  (given)
        "implicit", # observed by the machine (observation)
        "exmachina", # told (to the user) by the machine (told)
        "inferred", # evidence generated by inference (external or internal)
        "stereotype"] # evidence added by a stereotype


class Component:
    """ component object
        Identifier  the identifier of the component
                unique in the context
        Description readable description
        creation_time   time of creation of the component
        component_type  ["attribute", "activity", "knowledge", "belief", "preference", "goal"]
        value_type  ["string", "number","boolean", "enum", "JSON"]
        value_list    a list of strings that are the possible values for type "enum"
        value       the resolved value
        resolver    default resolver for this component
        goals       list of component paths eg [ ['Personal', 'Health', 'weight'], ...]
        evidencelist    list of evidence objects
    """
    def __init__(self, **kargs):
        # set some default values
        self.Identifier = None
        self.Description = ""
        self.component_type = None
        self.value_type = None
        self.value_list = []
        self.value = None
        self.resolver = None
        self.goals = []
        self.evidencelist = []
        self.objectType = "Component"
        self.creation_time = time.time()
        for k,v in kargs.items():
            self.__dict__[k] = v
        if self.Identifier == None:
            return None
        if not self.component_type in ComponentTypes:
            raise TypeError, "bad component type %s"%(self.component_type)
        if not self.value_type in ValueTypes:
            raise ValueError, "bad component value definition %s"%(self.value_type)
        if (self.value_type == "enum") and (len(self.value_list) == 0):
            raise ValueError, "type 'enum' requires non-empty value-list"
        if self.value != None:
            if (self.value_type == "enum") and not (self.value in self.value_list):
                raise ValueError, "value '%s' not in value_list for type 'enum'" % (self.value)

class Evidence:
    """ evidence object
        evidence_type   "explicit", # given by the user
                "implicit", # observed by the machine
                "exmachina", # told (to the user) by the machine
                "inferred", # evidence generated by a subscription inference 
                "stereotype"] # evidence added by a stereotype
        source  string indicating source of evidence
        value   any python object
        comment string with extra information about the evidence
        flags   a list of strings eg "goal"
        time    notional creation time optionally given by user
        creation_time actual time evidence item was created
        useby   timestamp evidence expires (if required)
    """
    def __init__(self, **kargs):
        self.flags = []
        self.evidence_type = None
        self.source = None
        self.owner = None
        self.value = None
        self.comment = None
        self.creation_time = None
        self.time = None  
        self.useby = None
        self.objectType = "Evidence"
        for k,v in kargs.items():
            self.__dict__[k] = v
        if not self.evidence_type in EvidenceTypes:
            raise TypeError, "bad evidence type %s"%(self.evidence_type)

    def __str__(self):
        return 'evidence: '+`self.__dict__`

class View:
    """ view object
        Identifier  the identifier of the component
                unique in the context
        Description readable description
    """
    def __init__(self, **kargs):
        self.Identifier = None
        self.Description = ""
        self.component_list = None
        self.objectType = "View"
        for k,v in kargs.items():
            self.__dict__[k] = v
        if self.Identifier == None:
            return None

class Context:
    """ context object
        Identifier  the identifier of the component
                unique in the context
        Description readable description
        resolver    default resolver for components in this context
    """
    def __init__(self, **kargs):
        # set some default values
        self.Identifier = None
        self.Description = ""
        self.perms = {} # permissions - owner only to begin
        self.resolver = None
        self.objectType = "Context"
        self.creation_time = time.time()
        for k,v in kargs.items():
            self.__dict__[k] = v
        if self.Identifier == None:
            return None

class Access(object):
    """
    Client version of access for client/server system

    arguments:
            model           model name
            modelserver     model server and port
            user            user name
            password        password string
    returns a user model access object
    """
    def __init__(self, connection=None, debug=0, test=True):
        self.debug =debug
        self.modelname = '-'
        self.user = ''
        self.password = ''
        self.connection = connection
        ok = False

        if not test: 
            return
        try:
            if self.debug != 0:
                print "jsondocall:", connection
            ok = do_call("access", {}, self.connection)
            if self.debug != 0:
                print "---------------------- result returned", ok
        except:
            if debug >0:
                traceback.print_exc()
            raise ValueError, "cannot access model"
        if not ok:
            raise ValueError, "server cannot access model"

    def ask(self,
            context=[],
            view=None,
            resolver=None,
            showcontexts=None):
        """
arguments: (see Personis_base for details)
        context is a list giving the path of context identifiers
        view is either:
                an identifier of a view in the context specified
                a list of component identifiers or full path lists
                None indicating that the values of all components in
                        the context be returned
        resolver specifies a resolver, default is the builtin resolver

returns a list of component objects
        """
        reslist = do_call("ask", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'view':view,\
                                                                        'resolver':resolver,\
                                                                        'showcontexts':showcontexts},
                                                                        self.connection)
        complist = []
        if showcontexts:
            cobjlist, contexts, theviews, thesubs = reslist
            for c in cobjlist:
                comp = Component(**c)
                if c["evidencelist"]:
                    comp.evidencelist = [Evidence(**e) for e in c["evidencelist"]]
                complist.append(comp)
            reslist = [complist, contexts, theviews, thesubs]
        else:
            for c in reslist:
                comp = Component(**c)
                if c["evidencelist"]:
                    comp.evidencelist = [Evidence(**e) for e in c["evidencelist"]]
                complist.append(comp)
            reslist = complist
        return reslist

    def tell(self,
            context=[],
            componentid=None,
            evidence=None):   # evidence obj
        """
arguments:
        context - a list giving the path to the required context
        componentid - identifier of the component
        evidence - evidence object to add to the component
        """
        if componentid == None:
            raise ValueError, "tell: componentid is None"
        if evidence == None:
            raise ValueError, "tell: no evidence provided"

        return do_call("tell", {'modelname':self.modelname,\
            'user':self.user,\
            'password':self.password,\
            'context':context,\
            'componentid':componentid,\
            'evidence':evidence.__dict__},
            self.connection
        )
    def mkcomponent(self,
            context=[],
            componentobj=None):
        """
Make a new component in a given context
arguments:
        context - a list giving the path to the required context
        componentobj - a Component object
returns:
        None on success
        a string error message on error
        """
        if componentobj == None:
            raise ValueError, "mkcomponent: componentobj is None"
        return do_call("mkcomponent", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'componentobj':componentobj.__dict__},
                                                                        self.connection)
    def delcomponent(self,
            context=[],
            componentid=None):
        """
Delete an existing component in a given context
arguments:
        context - a list giving the path to the required context
        id - the id for a componen
returns:
        None on success
        a string error message on error
        """
        if componentid == None:
            raise ValueError, "delcomponent: componentid is None"
        return do_call("delcomponent", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'componentid':componentid},
                                                                        self.connection)
    def delcontext(self,
            context=[]):
        """
Delete an existing context
arguments:
        context - a list giving the path to the required context
returns:
        None on success
        a string error message on error
        """
        if context == None:
            raise ValueError, "delcontext: context is None"
        return do_call( "delcontext", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context},
                                                                        self.connection)
    def getresolvers(self):
        '''Return a list of the available resolver names'''
        return do_call("getresolvers", {'modelname':self.modelname,\
                                                                        'user':self.user, 'password':self.password},
                                                                        self.connection)

    def setresolver(self,
            context,
            componentid,
            resolver):
        """
set the resolver for a given component in a given context
arguments:
        context - a list giving the path to the required context
        componentid - the id for a given component
        resolver - the id of the resolver
returns:
        None on success
        a string error message on error
        """
        if componentid == None:
            raise ValueError, "setresolver: componentid is None"
        return do_call("setresolver", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'componentid':componentid, \
                                                                        'resolver':resolver},
                                                                        self.connection)

    def mkview(self,
            context=[],
            viewobj=None):
        """
Make a new view in a given context
arguments:
        context - a list giving the path to the required context
        viewobj - a View object
returns:
        None on success
        a string error message on error
        """
        if viewobj == None:
            raise ValueError, "mkview: viewobj is None"
        return do_call("mkview", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'viewobj':viewobj.__dict__},
                                                                        self.connection)
    def delview(self,
            context=[],
            viewid=None):
        """
Delete an existing view in a given context
arguments:
        context - a list giving the path to the required context
        viewid - the id for the view
returns:
        None on success
        """
        if viewid == None:
            raise ValueError, "delview: viewid is None"
        return do_call("delview", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'viewid':viewid},
                                                                        self.connection)


    def mkcontext(self,
            context= [],
            contextobj=None):
        """
Make a new context in a given context
arguments:
        context - a list giving the path to the required context
        contextobj - a Context object
        """
        if contextobj == None:
            raise ValueError, "mkcontext: contextobj is None"
        return do_call("mkcontext", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'contextobj':contextobj.__dict__},
                                                                        self.connection)


    def getcontext(self,
            context=[],
            getsize=False):
        """
Get context information
arguments:
        context - a list giving the path to the required context
        getsize - True if the size in bytes of the context subtree is required
        """
        return do_call("getcontext", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'getsize':getsize},
                                                                        self.connection)

    def subscribe(self,
            context=[],
            view=None,
            subscription=None):
        """
arguments:
        context is a list giving the path of context identifiers
        view is either:
                an identifier of a view in the context specified
                a list of component identifiers or full path lists
                None indicating that the values of all components in
                        the context be returned
                subscription is a Subscription object
        """
        return  do_call("subscribe", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'view':view,\
                                                                        'subscription':subscription},
                                                                        self.connection)
    def delete_sub(self,
            context=[],
            componentid=None,
            subname=None):
        """
arguments:
        context is a list giving the path of context identifiers
        componentid designates the component subscribed to
        subname is the subscription name
        """
        return  do_call("delete_sub", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'componentid':componentid,\
                                                                        'subname':subname},
                                                                        self.connection)

    def export_model(self,
            context=[],
            resolver=None):
        """
arguments:
        context is the context to export
        resolver is a string containing the name of a resolver
                or
        resolver is a dictionary containing information about resolver(s) to be used and arguments
                the "resolver" key gives the name of a resolver to use, if not present the default resolver is used
                the "evidence_filter" key specifies an evidence filter
                eg 'evidence_filter' =  "all" returns all evidence,
                                        "last10" returns last 10 evidence items,
                                        "last1" returns most recent evidence item,
                                        None returns no evidence
        """
        return do_call("export_model", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'resolver':resolver},
                                                                        self.connection)

    def import_model(self,
            context=[],
            partial_model=None):
        """
arguments:
        context is the context to import into
        partial_model is a json encoded string containing the partial model
        """
        return do_call("import_model", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'partial_model':partial_model},
                                                                        self.connection)
    def set_goals(self,
            context=[],
            componentid=None,
            goals=None):
        """
arguments:
        context is a list giving the path of context identifiers
        componentid designates the component with subscriptions attached
        goals is a list of paths to components that are:
                goals for this componentid if it is not of type goal
                components that contribute to this componentid if it is of type goal
        """
        return  do_call("set_goals", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'componentid':componentid,\
                                                                        'goals':goals},
                                                                        self.connection)


    def list_subs(self,
            context=[],
            componentid=None):
        """
arguments:
        context is a list giving the path of context identifiers
        componentid designates the component with subscriptions attached
        """
        return  do_call("list_subs", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'componentid':componentid},
                                                                        self.connection)

    def registerapp(self, app=None, desc="", password=None):
        """
                registers a password for an app
                app name is a string (needs checking TODO)
                app passwords are stored at the top level .model db
        """
        return do_call("registerapp", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'app':app,\
                                                                        'description':desc,\
                                                                        'apppassword':password},
                                                                        self.connection)

    def deleteapp(self, app=None):
        """
                deletes an app
        """
        if app == None:
            raise ValueError, "deleteapp: app is None"
        return do_call("deleteapp", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'app':app},
                                                                        self.connection)

    def listapps(self):
        """
                returns array of registered app names
        """
        return do_call("listapps", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password},
                                                                        self.connection)

    def setpermission(self, context=None, componentid=None, app=None, permissions={}):
        """
                sets ask/tell permission for a context (if componentid is None) or
                        a component
        """
        return do_call("setpermission", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context': context,\
                                                                        'componentid': componentid,\
                                                                        'app': app,\
                                                                        'permissions': permissions},
                                                                        self.connection)

    def getpermission(self, context=None, componentid=None, app=None):
        """
gets permissions for a context (if componentid is None) or
a component
returns a tuple (ask,tell)
        """
        return do_call("getpermission", {'modelname':self.modelname,\
                                               'user':self.user,\
                                               'password':self.password,\
                                               'context': context,\
                                               'componentid': componentid,\
                                               'app': app},
                                               self.connection)