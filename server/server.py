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
import yaml
import jsoncall
import cherrypy
import base
import active
import util
import cPickle
from multiprocessing import Process, Queue
import cronserver
import random, time
import connection
from shove import Shove
import string

from mkmodel import *
#import httplib, oauth2
from optparse import OptionParser
import httplib2
import shutil

from oauth2client.file import Storage
from oauth2client.client import Storage, Credentials, OAuth2WebServerFlow, flow_from_clientsecrets
#from oauth2client.tools import run

from genshi.template import TemplateLoader
#loader = TemplateLoader('/templates', auto_reload=True)




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
        ok = jsoncall.do_call(modelserver, modelport, "mkmodel", {'modelname':modelname,\
                                                                'descripion':description,\
                                                                'user':user,\
                                                                'password':password})
    except:
        if debug >0:
            traceback.print_exc()
        raise ValueError, "cannot create model '%s', server '%s'" % (modelname, modelserver)
    if not ok:
        raise ValueError, "server '%s' cannot create model '%s'" % (modelserver, modelname)

class Access(active.Access):
    """
    Client version of access for client/server system

    arguments:
            model           model name
            modelserver     model server and port
            user            user name
            password        password string
    returns a user model access object
    """
    def __init__(self, modelname = '-', connection=None, debug=0):
        self.debug =debug
        self.modelname = modelname
        self.user = ''
        self.password = ''
        self.connection = connection
        ok = False

        try:
            if self.debug != 0:
                print "jsondocall:", connection
            ok = jsoncall.do_call("access", {}, self.connection)
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
arguments: (see base for details)
        context is a list giving the path of context identifiers
        view is either:
                an identifier of a view in the context specified
                a list of component identifiers or full path lists
                None indicating that the values of all components in
                        the context be returned
        resolver specifies a resolver, default is the builtin resolver

returns a list of component objects
        """
        reslist = jsoncall.do_call("ask", {'modelname':self.modelname,\
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
                comp = base.Component(**c)
                if c["evidencelist"]:
                    comp.evidencelist = [base.Evidence(**e) for e in c["evidencelist"]]
                complist.append(comp)
            reslist = [complist, contexts, theviews, thesubs]
        else:
            for c in reslist:
                comp = base.Component(**c)
                if c["evidencelist"]:
                    comp.evidencelist = [base.Evidence(**e) for e in c["evidencelist"]]
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

        return jsoncall.do_call("tell", {'modelname':self.modelname,\
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
        return jsoncall.do_call("mkcomponent", {'modelname':self.modelname,\
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
        return jsoncall.do_call("delcomponent", {'modelname':self.modelname,\
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
        return jsoncall.do_call( "delcontext", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context},
                                                                        self.connection)
    def getresolvers(self):
        '''Return a list of the available resolver names'''
        return jsoncall.do_call("getresolvers", {'modelname':self.modelname,\
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
        return jsoncall.do_call("setresolver", {'modelname':self.modelname,\
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
        return jsoncall.do_call("mkview", {'modelname':self.modelname,\
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
        return jsoncall.do_call("delview", {'modelname':self.modelname,\
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
        return jsoncall.do_call("mkcontext", {'modelname':self.modelname,\
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
        return jsoncall.do_call("getcontext", {'modelname':self.modelname,\
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
                subscription is a subscription object
        """
        return  jsoncall.do_call("subscribe", {'modelname':self.modelname,\
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
        return  jsoncall.do_call("delete_sub", {'modelname':self.modelname,\
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
        return jsoncall.do_call("export_model", {'modelname':self.modelname,\
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
        return jsoncall.do_call("import_model", {'modelname':self.modelname,\
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
        return  jsoncall.do_call("set_goals", {'modelname':self.modelname,\
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
        return  jsoncall.do_call("list_subs", {'modelname':self.modelname,\
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
        return jsoncall.do_call("registerapp", {'modelname':self.modelname,\
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
        return jsoncall.do_call("deleteapp", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'app':app},
                                                                        self.connection)

    def listapps(self):
        """
                returns array of registered app names
        """
        return jsoncall.do_call("listapps", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password},
                                                                        self.connection)

    def setpermission(self, context=None, componentid=None, app=None, permissions={}):
        """
                sets ask/tell permission for a context (if componentid is None) or
                        a component
        """
        return jsoncall.do_call("setpermission", {'modelname':self.modelname,\
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
        return jsoncall.do_call("getpermission", {'modelname':self.modelname,\
                                               'user':self.user,\
                                               'password':self.password,\
                                               'context': context,\
                                               'componentid': componentid,\
                                               'app': app},
                                               self.connection)


class oauth_client(object):

    def __init__(self, client_id, friendly_name, secret, redirect_uri, icon=''):
        self.client_id = client_id
        self.friendly_name = friendly_name
        self.secret = secret
        self.redirect_uri = redirect_uri
        self.icon = icon
        self.auth_codes = {}
        self.access_tokens = {}
        self.request_tokens = {}
        self.refresh_tokens = {}

    def __repr__(self):
        return '<%s %r>' % (type(self).__name__, self.client_id)

class server:

    def __init__(self, modeldir=None, adminsfile=None, oauthconfig=None):
        self.modeldir = modeldir
        self.admins = yaml.load(file(adminsfile,'r'))
        self.oauth_clients = Shove('sqlite:///oauth_clients.dat')
        self.access_tokens = Shove('sqlite:///oauth_access_tokens.dat')
        self.oauthconf = yaml.load(file(oauthconfig,'r'))

        def stopper():
            print 'saving persistant data'
            self.oauth_clients.close()
            self.access_tokens.close()
        cherrypy.engine.subscribe('stop', stopper)

    @cherrypy.expose
    def list_clients(self):
        """
        Admin interface for Personis. See admins.yaml for configuration
        (To be accessed by a user with a web browser)
        """
        # if we're here, we just want the local web UI. 
        # if no user then not logged in, so set admin to
        # true, target url back here, and go to login.
        if cherrypy.session.get('user') == None:
            cherrypy.session['admin'] = True
            cherrypy.session['target_url'] = '/list_clients'
            raise cherrypy.HTTPRedirect('/login')
        # check if user is actually allowed to be here
        if not cherrypy.session.get('user') in self.admins.keys():
            raise cherrypy.HTTPError(401, 'Admin only')

        base_path = os.path.dirname(os.path.abspath(__file__))
        loader = TemplateLoader([base_path])
        tmpl = loader.load('list_clients.html')
        for k, v in self.oauth_clients.items():
            print k, v.friendly_name
        stream = tmpl.generate(clients=self.oauth_clients.values())
        return stream.render('xhtml')


    @cherrypy.expose
    def list_apps(self):
        """
        App admin interface for Personis users. 
        (To be accessed by a user with a web browser)
        """
        # if we're here, we just want the local web UI. 
        # if no user then not logged in, so set admin to
        # true, target url back here, and go to login.
        if cherrypy.session.get('user') == None:
            cherrypy.session['admin'] = True
            cherrypy.session['target_url'] = '/list_apps'
            raise cherrypy.HTTPRedirect('/login')

        base_path = os.path.dirname(os.path.abspath(__file__))
        loader = TemplateLoader([base_path])
        tmpl = loader.load('list_apps.html')
        um = cherrypy.session.get('um')
        apps = um.listapps()
        for k in apps.keys():
            c = self.oauth_clients[k]
            apps[k]['friendly_name'] = c.friendly_name
            apps[k]['client_id'] = c.client_id
            apps[k]['icon'] = c.icon
        apps = [apps[k] for k in apps.keys()]
        print 'apps', apps
        stream = tmpl.generate(apps = apps)
        return stream.render('xhtml')

    @cherrypy.expose
    def list_apps_save(self, id, value, _method='get'):
        """
        AJAX helper for list_clients. No real user interface
        """
        if cherrypy.session.get('user') == None:
            raise cherrypy.HTTPError()
        # This uses a get parameter, where it should be del or post. 
        # worksfornow
        um = cherrypy.session.get('um')
        if id == "removeOneForMe":
            print "removed an app"
            um.deleteapp(value)
            raise cherrypy.HTTPRedirect('/list_apps')

    @cherrypy.expose
    def list_clients_save(self, id, value, _method='get'):
        """
        AJAX helper for list_clients. No real user interface
        """
        if cherrypy.session.get('user') == None:
            raise cherrypy.HTTPError()
        if not cherrypy.session.get('user') in self.admins.keys():
            raise cherrypy.HTTPError()
        # This uses a get parameter, where it should be del or post. 
        # worksfornow
        if id == "removeOneForMe":
            del(self.oauth_clients[value])
            self.oauth_clients.sync()
            print "removed a client"
            raise cherrypy.HTTPRedirect('/list_clients')
        if id == "addOneForMe":
            clid = u''
            secret = u''
            for i in range(32):
                clid = clid + random.choice(string.hexdigits)
                secret = secret + random.choice(string.hexdigits)
            self.oauth_clients[clid] = oauth_client(
                             client_id = clid,
                             friendly_name= 'my client',
                             secret= secret, 
                             redirect_uri='http://www.example.com/',
                             icon='/static/images/icon.svg')
            self.oauth_clients.sync()
            print "added a client"
            raise cherrypy.HTTPRedirect('/list_clients')

        clid, field = id.split('|')
        print 'saving: ',clid, field, value
        oldc = self.oauth_clients[clid]
        oldc.__dict__[field] = value
        self.oauth_clients[clid] = oldc
        for k, v in self.oauth_clients.items():
            print k, v.friendly_name
        self.oauth_clients.sync()
        return value
        
    @cherrypy.expose
    def authorize(self, client_id, redirect_uri, scope, access_type, response_type='code', approval_prompt='auto', state=None):
        """
        This is the entry point for client authentication against Personis. 
        (accessed by a user with a web browser, redirected from a client).
        Personis becomes an oauth2 server at this point. The session
        now contains the client_id but not much else.
        Only for oauth use. Don't come in this way if you want 
        to use list_clients!!
        """
        cherrypy.session['admin'] = False
        cherrypy.session['client_id'] = client_id
        
        cli = self.oauth_clients[client_id]
        if state <> None:
            cherrypy.session['state'] = state
        if cli.redirect_uri <> redirect_uri:
            raise cherrypy.HTTPError(400,'Redirect URIs do not match') 
        raise cherrypy.HTTPRedirect('/login')

    @cherrypy.expose
    def login(self):
        """
        Step 1.5. This is where clients of the personis web interface
        enter. there is no client_id etc because personis is not being
        used as an oauth server.
        """
        flow = flow_from_clientsecrets('client_secrets_google.json',
    scope='https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email')
        callback = cherrypy.request.base + '/logged_in'
        authorize_url = flow.step1_get_authorize_url(callback)
        cherrypy.session['flow'] = flow
        raise cherrypy.HTTPRedirect(authorize_url)

    @cherrypy.expose
    def logged_in(self, code):
        """
        Step 2 of the oauth dance. At this point Google has said this is a 
        known user. We then go and get more user info about them from google,
        save the info in a persistant store, create a model if none exists,
        and then ask them if they're happy to let the client they're using 
        access personis on their behalf.
        (Accessed by the user with a web browser redirected from /authorized)
        """
        flow = cherrypy.session.get('flow')
        if not flow:
            raise IOError()
        credentials = flow.step2_exchange(cherrypy.request.params)
        http = httplib2.Http()
        http = credentials.authorize(http)
        cjson = credentials.to_json()
        cjson = json.loads(cjson)
        content = http.request('https://www.googleapis.com/oauth2/v1/userinfo?access_token='+cjson['access_token'])
        #print 'content', content
        usr = json.loads(content[1])
        try:
            cherrypy.session['user'] = usr['id']
        except:
            print 'exception on usr', usr
            raise IOError()


        print 'loggedin session id',cherrypy.session.id

        # if no model for user, create one.
        if not os.path.exists(os.path.join(self.modeldir,usr['id'])):
            mkmodel(model=usr['id'], mfile='modeldefs/user.prod', modeldir=self.modeldir, user=usr['id'], password='')
            um = active.Access(model=usr['id'], modeldir=self.modeldir, user=usr['id'], password='')
            ev = base.Evidence(source="Create_Model", evidence_type="explicit", value=usr['given_name'])
            um.tell(context=["Personal"], componentid='firstname', evidence=ev)
            ev = base.Evidence(source="Create_Model", evidence_type="explicit", value=usr['family_name'])
            um.tell(context=["Personal"], componentid='lastname', evidence=ev)
            ev = base.Evidence(source="Create_Model", evidence_type="explicit", value=usr['gender'])
            um.tell(context=["Personal"], componentid='gender', evidence=ev)
            ev = base.Evidence(source="Create_Model", evidence_type="explicit", value=usr['email'])
            um.tell(context=["Personal"], componentid='email', evidence=ev)


            reslist = um.ask(context=["Personal"], view=['firstname','email'])
            util.printcomplist(reslist)

        um = active.Access(model=usr['id'], modeldir=self.modeldir, user=usr['id'], password='')
        try:
            reslist = um.ask(context=["Personal"], view=['picture'])
        except:
            #fill in missing icon info
            cobj = base.Component(Identifier="picture", component_type="attribute", value_type="string",resolver=None,Description="Uri of a picture of the user")
            um.mkcomponent(context=['Personal'], componentobj=cobj)
            ev = base.Evidence(source="Create_Model", evidence_type="explicit", value=usr['picture'])
            um.tell(context=["Personal"], componentid='picture', evidence=ev)

            reslist = um.ask(context=["Personal"], view=['firstname','picture'])
            util.printcomplist(reslist)

        # if we're here from a local url, just redirect. no need to allow.
        if cherrypy.session.get('admin'):
            cherrypy.session['um'] = um
            raise cherrypy.HTTPRedirect(cherrypy.session['target_url'])

        # if the app is already registered, it's ok.
        apps = um.listapps()
        print 'apps:',apps, 'clientid', cherrypy.session.get('client_id')
        if cherrypy.session.get('client_id') in apps:
            raise cherrypy.HTTPRedirect('/allow')

        #otherwise, ask yes/no                
        cli = self.oauth_clients[cherrypy.session['client_id']]
        base_path = os.path.dirname(os.path.abspath(__file__))
        loader = TemplateLoader([base_path])
        tmpl = loader.load('appQuery.html')
        stream = tmpl.generate(name=usr['given_name'], app=cli.friendly_name, icon=cli.icon, picture=usr['picture'])
        return stream.render('xhtml')

    @cherrypy.expose
    def allow(self):
        """
        In the case that they do want the client to use personis on their
        behalf, we register the client in um, and redirect back to the
        client with a temporary authorization key.
        (Accessed by a user with a web browser, redirected from /logged_in)
        """
        usrid = cherrypy.session.get('user')
        cli = self.oauth_clients[cherrypy.session.get('client_id')]

        val_key = ''
        for i in range(32):
            val_key = val_key+ random.choice(string.hexdigits)
        rdi = cli.redirect_uri + '?'
        if 'state' in cherrypy.session:
            rdi = rdi + 'state='+cherrypy.session['state']+'&amp;'
        rdi = rdi + 'code=' + val_key

        self.access_tokens[val_key] = {'timestamp': time.time(), 'userid': usrid, 'client_id': cherrypy.session['client_id'], 'type': 'authorization_code', 'expires': time.time()+600}
        self.access_tokens.sync()

        redr = cli.redirect_uri
        um = active.Access(model=usrid, modeldir=self.modeldir, user=usrid, password='')
        cherrypy.session['um'] = um
        result = um.registerapp(app=cherrypy.session['client_id'], desc=cli.friendly_name, password='')
        raise cherrypy.HTTPRedirect(rdi)
               
    @cherrypy.expose
    def dissallow(self):
        cli = self.oauth_clients[cherrypy.session.get('client_id')]
        redr = cli.redirect_uri+'?error=access_denied'
        #print redr
        raise cherrypy.HTTPRedirect(redr)

    @cherrypy.expose
    def request_token(self, client_id, client_secret, grant_type, code = None, redirect_uri = None, scope = None, refresh_token = None):
        """
        The client (mneme) has a temporary key (see /allow) but the key 
        has been to web browsers and back so it is not safe. It must be 
        exchanged by the client taking to personis directly (no web browser
        involvement) for a real token. Tokens have expiration dates etc.
        (Accessed by the client (Mneme, etc) on behalf of a user.)
        NOTE! This should only be exported over TLS/SSL (ahem!)
        """
        print 'code %s, redirui %s, clientid %s, clientsec %s, scope %s, granttype %s, refreshtoken %s'%(code, redirect_uri, client_id, client_secret, scope, grant_type, refresh_token)
        cli = self.oauth_clients[client_id]

        # expire old tokens before we look
        now = time.time()
        for k, v in self.access_tokens.items():
            #print 'access_tokens', k, 'v',v
            if now > v['expires']:
                #print 'expire access_token',k
                del(self.access_tokens[k])

        # temporary hack
        cli.access_tokens = cli.request_tokens

        if type(cli.secret) <> type(u''):
           cli.secret = unicode(cli.secret)

        if grant_type == 'refresh_token':
            code = refresh_token

        #for k,v in self.access_tokens.items():
            #print 'a:',k, v['type']

        if not code in self.access_tokens:
            if grant_type == 'refresh_token':
                raise cherrypy.HTTPError(401, 'Refresh_token expiry')
            else:
                raise cherrypy.HTTPError(401, 'Incorrect token')

        tok = self.access_tokens[code]

        if tok['client_id'] <> client_id:
            raise cherrypy.HTTPError(401, 'Incorrect client')

        #if tok['type'] == 'refresh_token':
            #print 'remove refresh_token',code
            #del(self.access_tokens[code])
        
        if cli.secret <> client_secret:
            raise cherrypy.HTTPError(401, 'Incorrect client information')

        userid = tok['userid']

        access_expiry =  3600 # an hour
        refresh_expiry = 3600*24*7*52 # a year

        access_token = ''
        access_token = ''.join([random.choice(string.hexdigits) for i in range(32)])
        self.access_tokens[access_token] = {'timestamp': time.time(), 'userid': userid, 'client_id': client_id, 'type': 'access_token', 'expires': time.time() + access_expiry}
        print 'added access_token:',access_token

        ret = {'access_token': access_token, 
               'token_type': 'bearer',
               'expires_in': access_expiry,
               "example_parameter":"example_value"
               }

        if grant_type == 'authorization_code':
            refresh_token = ''
            refresh_token = ''.join([random.choice(string.hexdigits) for i in range(32)])
            print 'added refresh_token:',refresh_token
            self.access_tokens[refresh_token] = {'timestamp': time.time(), 'userid': userid, 'client_id': client_id, 'type': 'refresh_token', 'expires': time.time() + refresh_expiry}
            ret['refresh_token'] = refresh_token

        self.access_tokens.sync()
        s = json.dumps(ret)
        print s
        return s


    @cherrypy.expose
    def default(self, *args, **kargs):

        cherrypy.session['admin'] = False

        cl = cherrypy.request.headers['Content-Length']
        jsonobj = cherrypy.request.body.read(int(cl))

        try:
            access_token = cherrypy.request.headers['Authorization'].split()[1]
            #print 'access_tokens', self.access_tokens
            #print 'access_token', `access_token`
        except:
            return '''
<h1>Personis</h1>
Looks like you're coming into the service entrance with a browser. That's not how it works. Ask someme about 'Mneme'. If you're an administrator, you might want to try <a href="/list_clients">the admin page</a>.
'''
        if not access_token in self.access_tokens:
	    raise cherrypy.HTTPError(401, 'Incorrect access token')
        #print 'token',self.access_tokens[access_token]
        now = time.time()
        if now > self.access_tokens[access_token]['expires']:
	    print 'expired', access_token
	    raise cherrypy.HTTPError(401, 'Expired access token')
        usr = self.access_tokens[access_token]['userid']
        
        try:
            pargs = json.loads(jsonobj)
        except:
            print "bad request - cannot decode json - possible access from web browser"
            return json.dumps("Personis User Model server. Not accessible using a web browser.")

        # dirty kludge to get around unicode
        for k,v in pargs.items():
            if type(v) == type(u''):
                pargs[k] = str(v)
            if type(k) == type(u''):
                del pargs[k]
                pargs[str(k)] = v

	model = usr
        if 'model' in pargs:
		model = pargs['modelname']

        print 'USER:', usr, 'MODEL:,', model, 'BEARER:', access_token

        try:
            result = False
            if args[0] == 'mkmodel':
                if not os.path.exists(os.path.join(self.modeldir,model)):
                    mkmodel(model=model, mfile='modeldefs/empty.prod', modeldir=self.modeldir, user=usr['id'], password='', description=pargs['description'])
                result = True
            else:
                um = active.Access(model=model, modeldir=self.modeldir, user=usr, password='')

            if args[0] == 'access':
                result = True
            elif args[0] == 'tell':
                result = um.tell(context=pargs['context'], componentid=pargs['componentid'], evidence=base.Evidence(**pargs['evidence']))
            elif args[0] == 'ask':
                reslist = um.ask(context=pargs['context'], view=pargs['view'], resolver=pargs['resolver'], \
                                        showcontexts=pargs['showcontexts'])
                if pargs['showcontexts']:
                    cobjlist, contexts, theviews, thesubs = reslist
                    cobjlist = [c.__dict__ for c in cobjlist]
                    for c in cobjlist:
                        if c["evidencelist"]:
                            c["evidencelist"] = [e for e in c["evidencelist"]]
                    newviews = {}
                    if theviews != None:
                        for vname,v in theviews.items():
                            newviews[vname] = v.__dict__
                    else:
                        newviews = None
                    reslist = [cobjlist, contexts, newviews, thesubs]
                else:
                    reslist = [c.__dict__ for c in reslist]
                    for c in reslist:
                        if c["evidencelist"]:
                            c["evidencelist"] = [e for e in c["evidencelist"]]
                result = reslist

            elif args[0] == 'subscribe':
                result = um.subscribe(context=pargs['context'], view=pargs['view'], subscription=pargs['subscription'])
            elif args[0] == 'delete_sub':
                result = um.delete_sub(context=pargs['context'], componentid=pargs['componentid'], subname=pargs['subname'])
            elif args[0] == 'list_subs':
                result = um.list_subs(context=pargs['context'], componentid=pargs['componentid'])
            elif args[0] == 'export_model':
                result = um.export_model(context=pargs['context'], resolver=pargs['resolver'])
            elif args[0] == 'import_model':
                result = um.import_model(context=pargs['context'], partial_model=pargs['partial_model'])
            elif args[0] == 'set_goals':
                result = um.set_goals(context=pargs['context'], componentid=pargs['componentid'], goals=pargs['goals'])
            elif args[0] == 'registerapp':
                result = um.registerapp(app=pargs['app'], desc=pargs['description'], password=pargs['apppassword'])
            elif args[0] == 'deleteapp':
                result = um.deleteapp(app=pargs['app'])
            elif args[0] == 'getpermission':
                result = um.getpermission(context=pargs['context'], componentid=pargs['componentid'], app=pargs['app'])
            elif args[0] == 'setpermission':
                result = um.setpermission(context=pargs['context'], componentid=pargs['componentid'], app=pargs['app'], permissions=pargs['permissions'])
            elif args[0] == 'listapps':
                result = um.listapps()
            elif args[0] == 'mkcomponent':
                comp = base.Component(**pargs["componentobj"])
                result = um.mkcomponent(pargs["context"], comp)
            elif args[0] == 'delcomponent':
                result = um.delcomponent(pargs["context"], pargs["componentid"])
            elif args[0] == 'delcontext':
                result = um.delcontext(pargs["context"])
            elif args[0] == 'setresolver':
                result = um.setresolver(pargs["context"], pargs["componentid"], pargs["resolver"])
            elif args[0] == 'getresolvers':
                result = um.getresolvers()
            elif args[0] == 'mkview':
                viewobj = base.View(**pargs["viewobj"])
                result = um.mkview(pargs["context"], viewobj)
            elif args[0] == 'delview':
                result = um.delview(pargs["context"], pargs["viewid"])
            elif args[0] == 'mkcontext':
                contextobj = base.Context(**pargs["contextobj"])
                result = um.mkcontext(pargs["context"], contextobj)
            elif args[0] == 'getcontext':
                result = um.getcontext(pargs["context"], pargs["getsize"])


            # Repackage result code with error values IF there is a version string.
            if pargs.has_key("version"):
                new_result = {}
                new_result["result"] = "ok"
                new_result["val"] = result
                result = new_result

        except Exception, e:

            print "Exception:", e
            traceback.print_exc()
            if pargs.has_key("version"):
                new_result = {}
                #new_result["errorType"] = e.__class__.__name__
                #new_result["errorData"] = e.__dict__.copy()
                #new_result["pythonPickel"] = cPickle.dumps(e)
                new_result["val"] = [e.__class__.__name__, e.__dict__.copy(), cPickle.dumps(e)]
                new_result["result"] = "error"
                result = new_result
            else:
                result = False

        return json.dumps(result)

def runServer(modeldir, config, admins, oauthconfig):
    print "serving models in '%s'" % (modeldir)
    print "config file '%s'" % (config)
    print "starting cronserver"
    cronserver.cronq = Queue()
    p = Process(target=cronserver.cronserver, args=(cronserver.cronq,modeldir))
    p.start()

    # ensure system model exists


    #conf = {'/favion.ico': {'tools.staticfile.on': True,'tools.staticfile.file': os.path.join(os.path.dirname(os.path.abspath(__file__)), '/images/favicon.ico')}}
    try:
        try:
            cherrypy.config.update(os.path.expanduser(config))
            cherrypy.tree.mount(Personis_server(modeldir, admins, oauthconfig), '/', config=config)
            #cherrypy.server.ssl_certificate = "server.crt"
            #cherrypy.server.ssl_private_key = "server.key" 
            cherrypy.engine.start()
            cherrypy.engine.block()
        except Exception, E:
            print "Failed to run Personis Server:" + str(E)
    finally:
        print "Shutting down Personis Server."
        cronserver.cronq.put(dict(op="quit"))
        p.join()


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-m", "--models", dest="modeldir",
              help="Model directory", metavar="DIRECTORY", default='models')
    parser.add_option("-c", "--config",
              dest="conf", metavar='FILE',
              help="Config file")
    parser.add_option("-a", "--admins",
              dest="admins", metavar='FILE',
              help="Admins file", default='admins.yaml')
    parser.add_option("-o", "--oauthconfig",
              dest="oauth", metavar='FILE',
              help="Oauth config file", default='oauth.yaml')

    (options, args) = parser.parse_args()
    runServer(options.modeldir, options.conf, options.admins, options.oauthconfig)
