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
from . import jsoncall
import cherrypy
from . import base
from . import active
from . import util
import cPickle
from multiprocessing import Process, Queue
from . import cronserver
import random, time
from . import connection
from shove import Shove
import string

from .mkmodel import *
from optparse import OptionParser
import httplib2
import logging
import shutil
import threading

from oauth2client.file import Storage
from oauth2client.client import Storage, Credentials, OAuth2WebServerFlow, flow_from_clientsecrets

from genshi.template import TemplateLoader

class Server:

    def __init__(self, modeldir='models', adminsfile='admins.yaml', clients = None, access_tokens='oauth_access_tokens.dat', client_secrets='client_secrets_google.json'):
        self.modeldir = modeldir
        self.admins = yaml.load(file(adminsfile,'r'))
        self.oauth_clients_file = clients
        self.client_secrets = client_secrets
        self.oauth_clients = json.loads(file(clients,'r').read())
        if self.oauth_clients == None:
            self.oauth_clients = {}
        self.access_tokens = Shove('sqlite:///'+access_tokens)

        def stopper():
            logging.info( 'saving persistant data')
            self.save_oauth_clients()
            self.access_tokens.close()
        cherrypy.engine.subscribe('stop', stopper)

    def save_oauth_clients(self):
        f = open(self.oauth_clients_file,'w')
        s = json.dumps(self.oauth_clients)
        f.write(s)
        f.close()

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
        if not cherrypy.session.get('user') in self.admins:
            raise cherrypy.HTTPError(401, 'Admin only')

        base_path = os.path.dirname(os.path.abspath(__file__))
        loader = TemplateLoader([base_path])
        tmpl = loader.load('html/list_clients.html')
        for k, v in self.oauth_clients.items():
            logging.debug( 'clients %s, %s', k, v['friendly_name'])
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
        tmpl = loader.load('html/list_apps.html')
        um = cherrypy.session.get('um')
        apps = um.listapps()
        for k in apps:
            c = self.oauth_clients[k]
            apps[k]['friendly_name'] = c['friendly_name']
            apps[k]['client_id'] = c['client_id']
            apps[k]['icon'] = c['icon']
        apps = [apps[k] for k in apps]
        logging.debug(  'apps %s', apps)
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
            logging.debug(  "removed an app")
            um.deleteapp(value)
            raise cherrypy.HTTPRedirect('/list_apps')

    @cherrypy.expose
    def list_clients_save(self, id, value, _method='get'):
        """
        AJAX helper for list_clients. No real user interface
        """
        if cherrypy.session.get('user') == None:
            raise cherrypy.HTTPError()
        if not cherrypy.session.get('user') in self.admins:
            raise cherrypy.HTTPError()
        # This uses a get parameter, where it should be del or post. 
        # worksfornow
        if id == "removeOneForMe":
            del(self.oauth_clients[value])
            self.save_oauth_clients()
            logging.debug(  "removed a client")
            raise cherrypy.HTTPRedirect('/list_clients')
        if id == "addOneForMe":
            clid = ''
            secret = ''
            for i in range(32):
                clid = clid + random.choice(string.hexdigits)
                secret = secret + random.choice(string.hexdigits)
            self.oauth_clients[clid] = {
                             'client_id': clid,
                             'friendly_name': 'my client',
                             'secret': secret, 
                             'redirect_uri': 'http://www.example.com/',
                             'icon': '/static/images/icon.svg'}
            self.save_oauth_clients()
            logging.debug(  "added a client")
            raise cherrypy.HTTPRedirect('/list_clients')

        clid, field = id.split('|')
        logging.debug(  'saving: ',clid, field, value)
        oldc = self.oauth_clients[clid][field] = value
        for k, v in self.oauth_clients.items():
            logging.debug(  k, v['friendly_name'])
        self.save_oauth_clients()
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
        if state != None:
            cherrypy.session['state'] = state
        if cli['redirect_uri'] != redirect_uri:
            logging.debug("redirect uris don't match expected %s got %s",cli['redirect_uri'], redirect_uri)
            raise cherrypy.HTTPError(400,'Redirect URIs do not match') 
        raise cherrypy.HTTPRedirect('/login')

    @cherrypy.expose
    def login(self):
        """
        Step 1.5. This is where clients of the personis web interface
        enter. there is no client_id etc because personis is not being
        used as an oauth server.
        """
        flow = flow_from_clientsecrets(self.client_secrets,
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
        try:
            usr = json.loads(content[1])
            user = usr['email'].split('@')[0].replace('.','')
            cherrypy.session['user'] = user
        except:
            logging.debug(  'exception on usr %s', content[1])
            raise IOError()


        logging.debug(  'loggedin session id %s',cherrypy.session.id)

        if not 'picture' in usr:
            if usr['gender'].lower() == 'male':
                usr['picture'] = 'http://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/161px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg'
            else:
                usr['picture'] = 'http://www.lacasadeviena.com/wp-content/uploads/2012/06/magritte-sonofman1-300x362.jpg'

        # if no model for user, create one.
        if not os.path.exists(os.path.join(self.modeldir,user)):
            mf = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modeldefs/user.prod')
            mkmodel(model=user, mfile=mf, modeldir=self.modeldir, user=user, password='')
            um = active.Access(model=user, modeldir=self.modeldir, user=user, password='')
            ev = base.Evidence(source="Create_Model", evidence_type="explicit", value=usr['given_name'])
            um.tell(context=["Personal"], componentid='firstname', evidence=ev)
            ev = base.Evidence(source="Create_Model", evidence_type="explicit", value=usr['family_name'])
            um.tell(context=["Personal"], componentid='lastname', evidence=ev)
            ev = base.Evidence(source="Create_Model", evidence_type="explicit", value=usr['gender'])
            um.tell(context=["Personal"], componentid='gender', evidence=ev)
            ev = base.Evidence(source="Create_Model", evidence_type="explicit", value=usr['email'])
            um.tell(context=["Personal"], componentid='email', evidence=ev)
            ev = base.Evidence(source="Create_Model", evidence_type="explicit", value=usr['id'])
            um.tell(context=["Personal"], componentid='gid', evidence=ev)
            ev = base.Evidence(source="Create_Model", evidence_type="explicit", value=usr['picture'])
            um.tell(context=["Personal"], componentid='picture', evidence=ev)


            reslist = um.ask(context=["Personal"], view=['firstname','email'])
            util.printcomplist(reslist)

        um = active.Access(model=user, modeldir=self.modeldir, user=user, password='')
        
        # if we're here from a local url, just redirect. no need to allow.
        if cherrypy.session.get('admin'):
            cherrypy.session['um'] = um
            raise cherrypy.HTTPRedirect(cherrypy.session['target_url'])

        # if the app is already registered, it's ok.
        apps = um.listapps()
        logging.debug(  'apps: %s, clientid: %s', apps, cherrypy.session.get('client_id'))
        if cherrypy.session.get('client_id') in apps:
            raise cherrypy.HTTPRedirect('/allow')

        #otherwise, ask yes/no                
        cli = self.oauth_clients[cherrypy.session['client_id']]
        base_path = os.path.dirname(os.path.abspath(__file__))
        loader = TemplateLoader([os.path.join(base_path, 'html')])
        tmpl = loader.load('appQuery.html')
        stream = tmpl.generate(name=usr['given_name'], app=cli['friendly_name'], icon=cli['icon'], picture=usr['picture'])
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
        rdi = cli['redirect_uri'] + '?'
        if 'state' in cherrypy.session:
            rdi = rdi + 'state='+cherrypy.session['state']+'&amp;'
        rdi = rdi + 'code=' + val_key

        self.access_tokens[val_key] = {'timestamp': time.time(), 'userid': usrid, 'client_id': cherrypy.session['client_id'], 'type': 'authorization_code', 'expires': time.time()+600}
        self.access_tokens.sync()
        logging.debug('access tokens: %s',repr([i for i in self.access_tokens.keys()]))

        redr = cli['redirect_uri']
        um = active.Access(model=usrid, modeldir=self.modeldir, user=usrid, password='')
        cherrypy.session['um'] = um
        result = um.registerapp(app=cherrypy.session['client_id'], desc=cli['friendly_name'], password='')
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
        logging.debug(  'code %s, redirui %s, clientid %s, clientsec %s, scope %s, granttype %s, refreshtoken %s'%(code, redirect_uri, client_id, client_secret, scope, grant_type, refresh_token))
        cli = self.oauth_clients[client_id]

        # expire old tokens before we look
        now = time.time()
        for k, v in self.access_tokens.items():
            logging.debug(  'access_tokens %s: %s', k,v)
            if now > v['expires']:
                logging.debug (  'expire access_token %s',k)
                del(self.access_tokens[k])

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

        if tok['client_id'] != client_id:
            raise cherrypy.HTTPError(401, 'Incorrect client')

        #if tok['type'] == 'refresh_token':
            #print 'remove refresh_token',code
            #del(self.access_tokens[code])
        
        if cli['secret'] != client_secret:
            raise cherrypy.HTTPError(401, 'Incorrect client information')

        userid = tok['userid']

        access_expiry =  3600 # an hour
        refresh_expiry = 3600*24*7*52 *20 # a year

        access_token = ''
        access_token = ''.join([random.choice(string.hexdigits) for i in range(32)])
        self.access_tokens[access_token] = {'timestamp': time.time(), 'userid': userid, 'client_id': client_id, 'type': 'access_token', 'expires': time.time() + access_expiry}
        logging.debug(  'added access_token: %s',access_token)

        ret = {'access_token': access_token, 
               'token_type': 'bearer',
               'expires_in': access_expiry,
               "example_parameter":"example_value"
               }

        if grant_type == 'authorization_code':
            refresh_token = ''
            refresh_token = ''.join([random.choice(string.hexdigits) for i in range(32)])
            logging.info(  'added refresh_token: %s',refresh_token)
            self.access_tokens[refresh_token] = {'timestamp': time.time(), 'userid': userid, 'client_id': client_id, 'type': 'refresh_token', 'expires': time.time() + refresh_expiry}
            ret['refresh_token'] = refresh_token

        self.access_tokens.sync()
        s = json.dumps(ret)
        logging.info(  s)
        return s


    @cherrypy.expose
    def default(self, *args, **kargs):

        cherrypy.session['admin'] = False

        try:
            access_token = cherrypy.request.headers['Authorization'].split()[1]
            logging.debug( 'access_tokens %s', self.access_tokens )
            logging.debug(  'access_token %s', repr(access_token) )
        except:
            return '''
<h1>Personis</h1>
Looks like you're coming into the service entrance with a browser, which is not how this works. Ask someme about 'Mneme', or perhaps you're looking for <a href="/list_apps">your apps</a>.
<br/>If you're an administrator, you might want to try <a href="/list_clients">the admin page</a>, or the <a href="/doc/index.html">the docs</a>.
<br/>Source at <a href="https://github.com/jbu/personis">github</a>.
'''
        if not access_token in self.access_tokens:
    	    raise cherrypy.HTTPError(401, 'Incorrect access token')
            #print 'token',self.access_tokens[access_token]
        now = time.time()
        if now > self.access_tokens[access_token]['expires']:
	       logging.debug(  'expired %s', access_token)
	       raise cherrypy.HTTPError(401, 'Expired access token')
    
        usr = self.access_tokens[access_token]['userid']

        cl = cherrypy.request.headers['Content-Length']
        jsonobj = cherrypy.request.body.read(int(cl))
        
        try:
            pargs = json.loads(jsonobj)
        except:
            logging.debug(  "bad request - cannot decode json - possible access from web browser")
            return json.dumps("Personis User Model server. Not accessible using a web browser.")

        # dirty kludge to get around unicode
        for k,v in pargs.items():
            if type(v) == type(''):
                pargs[k] = str(v)
            if type(k) == type(''):
                del pargs[k]
                pargs[str(k)] = v

        model = usr
        if 'model' in pargs:
		model = pargs['modelname']

        logging.debug(  'USER: %s, MODEL: %s, BEARER: %s', usr, model, access_token)

        try:
            result = False
            if args[0] == 'mkmodel':
                if not os.path.exists(os.path.join(self.modeldir,model)):
                    mkmodel(model=model, mfile='modeldefs/empty.prod', modeldir=self.modeldir, user=usr['id'], password='', description=pargs['description'])
                result = True
            else:
                um = active.Access(model=model, modeldir=self.modeldir, user=usr, password='')

            apps = um.listapps()
            if not self.access_tokens[access_token]['client_id'] in apps:
                logging.debug(  'client for access token not in model %s, %s', access_token, self.access_tokens[access_token]['client_id'])
                raise cherrypy.HTTPError(401, 'client for access token not in model')

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
            if 'version' in pargs:
                new_result = {}
                new_result["result"] = "ok"
                new_result["val"] = result
                result = new_result

        except Exception as e:

            logging.info(  "Exception: %s", e)
            traceback.print_exc()
            if 'version' in pargs:
                new_result = {}
                new_result["val"] = [e.__class__.__name__, e.__dict__.copy(), cPickle.dumps(e)]
                new_result["result"] = "error"
                result = new_result
            else:
                result = False

        return json.dumps(result)

class ExitThread(threading.Thread):
    def __init__(self, cp, cronp, cronqueue, queue):
        self.cp = cp
        self.q = queue
        self.cronq = cronqueue
        self.cronp = cronp

    def run(self):
        self.running = True
        print('exit thread running')
        logging.info('exit listener running')
        while self.running:
            g = self.q.get(block = True)
            logging.info('exit thread got %s', g)
            if g == 'exit':
                self.running = False
            print('qgot', g)
        logging.info('exit listener run ends')
        self.exit()

    def exit(self):
        logging.info(  "Shutting down Personis Server. - exit thread")
        self.cronq.put(dict(op="quit"))
        self.cronp.join()
        self.cp.engine.exit()
        self.join()

def runServer(modeldir, config, admins, clients, tokens, loglevel=logging.INFO, exit_queue = None, client_secrets = 'client_secrets_google.json'):
    logging.basicConfig(level=loglevel)
    logging.info(  "serving models in '%s'" % (modeldir))
    logging.info(  "config file '%s'" % (config))
    logging.info(  "admin file '%s'" % (admins))
    logging.info(  "clients file '%s'" % (clients))
    logging.info(  "tokens file '%s'" % (tokens))
    logging.info(  "client secrets file '%s'" % (client_secrets))
    logging.info(  "starting cronserver")
    cronserver.cronq = Queue()
    p = Process(target=cronserver.cronserver, args=(cronserver.cronq,modeldir))
    p.start()

    if exit_queue:
        e = ExitThread(cherrypy, p, cronserver.cronq, exit_queue)

    try:
        try:
            cherrypy.config.update(os.path.expanduser(config))
            cherrypy.tree.mount(Server(modeldir, admins, clients, tokens, client_secrets), '/', config=config)
            #cherrypy.server.ssl_certificate = "server.crt"
            #cherrypy.server.ssl_private_key = "server.key" 
            cherrypy.engine.start()
            if not exit_queue:
                cherrypy.engine.block()
            else:
                e.start()
        except Exception as E:
            logging.info(  "Failed to run Personis Server:" + str(E))
    finally:
        if exit_queue:
            exit_queue.put('exit')
        else:
            logging.info(  "Shutting down Personis Server.")
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
    parser.add_option("-o", "--oauthclients",
              dest="clients", metavar='FILE',
              help="Clients json file", default='oauth_clients.json')
    parser.add_option("-t", "--tokens",
              dest="tokens", metavar='FILE',
              help="Access tokens database", default='oauth_access_tokens.dat')
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
