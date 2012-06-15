#!/usr/bin/env python

#
# The Personis system is copyright 2000-2011 University of Sydney
#       Bob.Kummerfeld@Sydney.edu.au
# GPL v3
#
# Active User Models: added subscribe method to Access
#

import os, traceback
import json
import jsoncall
import cherrypy
import Personis_base
import Personis_a
import Personis_util
import cPickle
from multiprocessing import Process, Queue
import cronserver
import random, time

from Personis_mkmodel import *
#import httplib, oauth2
from optparse import OptionParser
import httplib2
import shutil

from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError, Storage, Credentials, OAuth2WebServerFlow
from oauth2client.tools import run




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

class Access(Personis_a.Access):
    """
    Client version of access for client/server system

    arguments:
            model           model name
            modelserver     model server and port
            user            user name
            password        password string
    returns a user model access object
    """
    def __init__(self, credentials=None, debug=0):
        self.debug =debug
        self.modelname = '-'
        self.user = ''
        self.password = ''
        self.credentials = credentials
        ok = False

        try:
            if self.debug != 0:
                print "jsondocall:", credentials
            ok = jsoncall.do_call(credentials, "access", {})
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
        reslist = jsoncall.do_call(self.credentials, "ask", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'view':view,\
                                                                        'resolver':resolver,\
                                                                        'showcontexts':showcontexts})
        complist = []
        if showcontexts:
            cobjlist, contexts, theviews, thesubs = reslist
            for c in cobjlist:
                comp = Personis_base.Component(**c)
                if c["evidencelist"]:
                    comp.evidencelist = [Personis_base.Evidence(**e) for e in c["evidencelist"]]
                complist.append(comp)
            reslist = [complist, contexts, theviews, thesubs]
        else:
            for c in reslist:
                comp = Personis_base.Component(**c)
                if c["evidencelist"]:
                    comp.evidencelist = [Personis_base.Evidence(**e) for e in c["evidencelist"]]
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

        return jsoncall.do_call(self.credentials, "tell", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'componentid':componentid,\
                                                                        'evidence':evidence.__dict__})
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
        return jsoncall.do_call(self.credentials, "mkcomponent", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'componentobj':componentobj.__dict__})
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
        return jsoncall.do_call(self.credentials, "delcomponent", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'componentid':componentid})
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
        return jsoncall.do_call(self.credentials, "delcontext", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context})
    def getresolvers(self):
        '''Return a list of the available resolver names'''
        return jsoncall.do_call(self.credentials, "getresolvers", {'modelname':self.modelname,\
                                                                        'user':self.user, 'password':self.password})

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
        return jsoncall.do_call(self.credentials, "setresolver", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'componentid':componentid, \
                                                                        'resolver':resolver})

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
        return jsoncall.do_call(self.credentials, "mkview", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'viewobj':viewobj.__dict__})
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
        return jsoncall.do_call(self.credentials, "delview", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'viewid':viewid})


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
        return jsoncall.do_call(self.credentials, "mkcontext", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'contextobj':contextobj.__dict__})


    def getcontext(self,
            context=[],
            getsize=False):
        """
Get context information
arguments:
        context - a list giving the path to the required context
        getsize - True if the size in bytes of the context subtree is required
        """
        return jsoncall.do_call(self.credentials, "getcontext", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'getsize':getsize})

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
        return  jsoncall.do_call(self.credentials, "subscribe", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'view':view,\
                                                                        'subscription':subscription})
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
        return  jsoncall.do_call(self.credentials, "delete_sub", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'componentid':componentid,\
                                                                        'subname':subname})

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
        return jsoncall.do_call(self.credentials, "export_model", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'resolver':resolver})

    def import_model(self,
            context=[],
            partial_model=None):
        """
arguments:
        context is the context to import into
        partial_model is a json encoded string containing the partial model
        """
        return jsoncall.do_call(self.credentials, "import_model", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'partial_model':partial_model})
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
        return  jsoncall.do_call(self.credentials, "set_goals", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'componentid':componentid,\
                                                                        'goals':goals})


    def list_subs(self,
            context=[],
            componentid=None):
        """
arguments:
        context is a list giving the path of context identifiers
        componentid designates the component with subscriptions attached
        """
        return  jsoncall.do_call(self.credentials, "list_subs", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context':context,\
                                                                        'componentid':componentid})

    def registerapp(self, app=None, desc="", password=None):
        """
                registers a password for an app
                app name is a string (needs checking TODO)
                app passwords are stored at the top level .model db
        """
        return jsoncall.do_call(self.credentials, "registerapp", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'app':app,\
                                                                        'description':desc,\
                                                                        'apppassword':password})

    def deleteapp(self, app=None):
        """
                deletes an app
        """
        if app == None:
            raise ValueError, "deleteapp: app is None"
        return jsoncall.do_call(self.credentials, "deleteapp", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'app':app})

    def listapps(self):
        """
                returns array of registered app names
        """
        return jsoncall.do_call(self.credentials, "listapps", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password})

    def setpermission(self, context=None, componentid=None, app=None, permissions={}):
        """
                sets ask/tell permission for a context (if componentid is None) or
                        a component
        """
        return jsoncall.do_call(self.credentials, "setpermission", {'modelname':self.modelname,\
                                                                        'user':self.user,\
                                                                        'password':self.password,\
                                                                        'context': context,\
                                                                        'componentid': componentid,\
                                                                        'app': app,\
                                                                        'permissions': permissions})

    def getpermission(self, context=None, componentid=None, app=None):
        """
gets permissions for a context (if componentid is None) or
a component
returns a tuple (ask,tell)
        """
        return jsoncall.do_call(self.credentials, "getpermission", {'modelname':self.modelname,\
                                               'user':self.user,\
                                               'password':self.password,\
                                               'context': context,\
                                               'componentid': componentid,\
                                               'app': app})


      



oauth_consumers = {'personis_client_mneme': {
                                             'friendly_name': 'Mneme',
                                             'secret': 'personis_client_secret_mneme', 
                                             'redirect_uri': 'http://enterprise.it.usyd.edu.au:8000/authorized',
                                             'auth_codes': {},
                                             'request_tokens': {},
                                             'refresh_tokens': {}
                                             },
                   'personis_client_log_llum': {
                                             'friendly_name': 'Log',
                                             'secret': 'personis_client_secret_log_llum', 
                                             'redirect_uri': 'http://enterprise.it.usyd.edu.au:8001/authorized',
                                             'auth_codes': {},
                                             'request_tokens': {},
                                             'refresh_tokens': {}
                                             },
                   'personis_client_umbrowse': {
                                             'friendly_name': 'Umbrowse',
                                             'secret': 'personis_client_secret_umbrowse', 
                                             'redirect_uri': 'http://localhost:8080/',
                                             'auth_codes': {},
                                             'request_tokens': {},
                                             'refresh_tokens': {}
                                             }
                   }

users = {}

bearers = {}

class Personis_server:

    auth__doc = "The object that serves authentication pages"

    def __init__(self, modeldir=None):
        self.modeldir = modeldir

    @cherrypy.expose
    def authorize(self, client_id, redirect_uri, scope, access_type, response_type='code', approval_prompt='auto', state=None):
        body = cherrypy.request.body.fp.read()
        rurl = cherrypy.request.base+cherrypy.request.path_info

        cherrypy.session['client_id'] = client_id
        print response_type, client_id, scope, access_type, approval_prompt
        
        cli = oauth_consumers[client_id]
        if state <> None:
            cherrypy.session['state'] = state
        if cli['redirect_uri'] <> redirect_uri:
            raise cherrypy.HTTPError() 
        raise cherrypy.HTTPRedirect('/login')
    
    @cherrypy.expose
    def login(self):
        flow = OAuth2WebServerFlow(client_id='911883322662-kbpqhupbua19n373cj7sssurg4ebg09p.apps.googleusercontent.com',
                                   client_secret='Isd22yV2-1YyfOoXgJeR3EtM',
                                   scope='https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email',
                                   user_agent='personis-server/1.0')
        callback = callback = cherrypy.request.base + '/logged_in'
        authorize_url = flow.step1_get_authorize_url(callback)
        cherrypy.session['flow'] = flow
        raise cherrypy.HTTPRedirect(authorize_url)

    @cherrypy.expose
    def logged_in(self, code):
        user = cherrypy.session.get('user')
        flow = cherrypy.session.get('flow')
        if not flow:
            raise IOError()
        credentials = flow.step2_exchange(cherrypy.request.params)
        cherrypy.session['credentials'] = credentials
        http = httplib2.Http()
        http = credentials.authorize(http)
        cjson = credentials.to_json()
        cjson = json.loads(cjson)
        content = http.request('https://www.googleapis.com/oauth2/v1/userinfo?access_token='+cjson['access_token'])
        #print 'content', content
        usr = json.loads(content[1])
        cherrypy.session['user'] = usr
        users[usr['id']] = [usr, credentials]
        print 'session',cherrypy.session.id
        print 'got user',usr
        
        
        cli = oauth_consumers[cherrypy.session['client_id']]
        print 'loggedin session id',cherrypy.session.id

        # if no model for user, create one.
        if not os.path.exists(os.path.join(self.modeldir,usr['id'])):
            fn = os.path.join('tmp',usr['id'])
            #f1 = open('Modeldefs/user.template','r').read()
            #f = open(fn, 'w')
            #f.write(f1%(usr['given_name'],usr['family_name'], usr['gender'], usr['email']))
            #f.close()
            mkmodel(model=usr['id'], mfile='Modeldefs/user.prod', modeldir=self.modeldir, user=usr['id'], password='')
            um = Personis_a.Access(model=usr['id'], modeldir=self.modeldir, user=usr['id'], password='')
            ev = Personis_base.Evidence(source="Create_Model", evidence_type="explicit", value=usr['given_name'])
            um.tell(context=["Personal"], componentid='firstname', evidence=ev)
            ev = Personis_base.Evidence(source="Create_Model", evidence_type="explicit", value=usr['family_name'])
            um.tell(context=["Personal"], componentid='lastname', evidence=ev)
            ev = Personis_base.Evidence(source="Create_Model", evidence_type="explicit", value=usr['gender'])
            um.tell(context=["Personal"], componentid='gender', evidence=ev)
            ev = Personis_base.Evidence(source="Create_Model", evidence_type="explicit", value=usr['email'])
            um.tell(context=["Personal"], componentid='email', evidence=ev)
            reslist = um.ask(context=["Personal"], view=['firstname','email'])
            Personis_util.printcomplist(reslist)

        # if it's mneme, then don't ask whether it's all ok. just do it.
        if cli['secret'] == 'personis_client_secret_mneme':
            raise cherrypy.HTTPRedirect('/allow')
        
        #otherwise, ask yes/no                
        return '''
        <body>
        <h1>Welcome %s!</h1>
        The %s application is requesting access to your model. Do you want to allow this?
        <br>
        <a href="/allow">yes</a>, <a href="dissallow">no</a>
        </body>
        '''%(usr['given_name'], cli['friendly_name'])

    @cherrypy.expose
    def allow(self):
        print 'allow session id',cherrypy.session.id
        usr = cherrypy.session.get('user')
        print usr
        val_key = ''
        for i in range(10):
            val_key = val_key+ str(int(random.random()*100))
        cli = oauth_consumers[cherrypy.session['client_id']]
        rdi = cli['redirect_uri'] + '?'
        if cherrypy.session.has_key('state'):
            rdi = rdi + 'state='+cherrypy.session['state']+'&amp;'
        rdi = rdi + 'code=' + val_key
        cherrypy.session['auth_code'] = val_key
        cli['auth_codes'][val_key] = [time.time(),usr['id']]

        cli = oauth_consumers[cherrypy.session.get('client_id')]
        redr = cli['redirect_uri']
        print redr, cherrypy.session.get('auth_code')
        raise cherrypy.HTTPRedirect(redr+'?code='+cherrypy.session.get('auth_code'))
               
    @cherrypy.expose
    def dissallow(self):
        cli = oauth_consumers[cherrypy.session.get('client_id')]
        redr = cli['redirect_uri']+'?error=access_denied'
        #print redr
        raise cherrypy.HTTPRedirect(redr)

    @cherrypy.expose
    def request_token(self, code, redirect_uri, client_id, client_secret, scope, grant_type):
        #nasty hack. insecure. needs to check code!
        cli = oauth_consumers[client_id]
        #code = code.encode('ascii')
        #print 'code:',code
        #print 'client:',cli
        #print 'users:',users
        if not cli['auth_codes'].has_key(code):
            raise cherrypy.HTTPError()
        atoken = ''
        rtoken = ''
        for i in range(10):
            atoken = atoken + str(int(random.random()*100))
            rtoken = rtoken + str(int(random.random()*100))
        user = users[cli['auth_codes'][code][1]][0]
        b = {}
        b['user'] = user
        b['credentials'] = users[cli['auth_codes'][code][1]][1]
        bearers[atoken] = b
        #print user
        cli['request_tokens'][atoken] = user['id']
        cli['refresh_tokens'][rtoken] = ''
        s = '''
{
    "access_token":"%s",
    "token_type":"bearer",
    "expires_in":3600,
    "refresh_token":"%s",
    "example_parameter":"example_value"
}
        '''%(atoken,rtoken)
        del(users[cli['auth_codes'][code][1]])
        del(cli['auth_codes'][code])
        print s
        return s

    @cherrypy.expose
    def default(self, *args):

        print 'path', cherrypy.request.path_info
        #print 'method', cherrypy.request.method
        #print 'headers', cherrypy.request.headers
        #print 'args', args
        #print 'params', cherrypy.request.params        
        jsonobj = cherrypy.request.body.fp.read()        
        print 'body', jsonobj

        #if cherrypy.session.get('user') == None:
        #    raise cherrypy.HTTPRedirect('/login')
        try:
            print cherrypy.request.headers['Authorization']
            access_token = cherrypy.request.headers['Authorization'].split()[1]
            usr = bearers[access_token]['user']
            print 'user:',usr['id']
        except:
            raise cherrypy.HTTPError()
        
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

        try:
            result = False
            if args[0] == 'mkmodel':
                # fixme need to implement security
                # and error handling
                Personis_base.MkModel(model=usr['id'], modeldir=self.modeldir, \
                                        user=usr['id'], password='', description=pargs['description'])
                result = True
            else:
                um = Personis_a.Access(model=usr['id'], modeldir=self.modeldir, user=usr['id'], password='')

            if args[0] == 'access':
                result = True
            elif args[0] == 'tell':
                result = um.tell(context=pargs['context'], componentid=pargs['componentid'], evidence=Personis_base.Evidence(**pargs['evidence']))
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
                comp = Personis_base.Component(**pargs["componentobj"])
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
                viewobj = Personis_base.View(**pargs["viewobj"])
                result = um.mkview(pargs["context"], viewobj)
            elif args[0] == 'delview':
                result = um.delview(pargs["context"], pargs["viewid"])
            elif args[0] == 'mkcontext':
                contextobj = Personis_base.Context(**pargs["contextobj"])
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

#Restrict default access to logged in users
#@lg_authority.groups('auth')
class Root(object):
    """CherryPy server root"""

    auth__doc = "The object that serves authentication pages"

    #Allow everyone to see the index page
    @cherrypy.expose
#       @lg_authority.groups('any')
    def index(self):
        return '<p>Welcome!</p><p>Would you like to <a href="protected">view protected information?</a></p>'

    #This method inherits restricted access from the Root class it belongs to
    @cherrypy.expose
    def protected(self):
        return '<p>Welcome, {user}!</p><p><a href="auth/logout">Logout</a> and try again?<p>'.format(user=cherrypy.user.id)


def runServer(modeldir, config):
    print "serving models in '%s'" % (modeldir)
    print "config file '%s'" % (config)
    print "starting cronserver"
    cronserver.cronq = Queue()
    p = Process(target=cronserver.cronserver, args=(cronserver.cronq,modeldir))
    p.start()
    #conf = {'/favion.ico': {'tools.staticfile.on': True,'tools.staticfile.file': os.path.join(os.path.dirname(os.path.abspath(__file__)), '/images/favicon.ico')}}
    try:
        try:
            cherrypy.config.update(os.path.expanduser(config))
            cherrypy.tree.mount(Personis_server(modeldir), '/', config=config)
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

    (options, args) = parser.parse_args()
    runServer(options.modeldir, options.conf)
