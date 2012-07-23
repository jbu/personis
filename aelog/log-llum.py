import os, sys

from oauth2client.file import Storage
from oauth2client.client import Storage, Credentials, OAuth2WebServerFlow, AccessTokenRefreshError
from oauth2client.tools import run

import httplib
import httplib2
import webapp2
from gaesessions import get_current_session

import personis
import yaml
import time
import logging
import pickle

item_list = {'apple':{'icon':'http://appleadayproject.files.wordpress.com/2011/03/apple-full2.jpg'},
            'pear':{'icon': 'http://4.bp.blogspot.com/-IgzE0L2YSdg/T1Pg-z8t6-I/AAAAAAAAAhU/cWfds0ulbLI/s1600/Pear.jpg'}, 
            'banana':{'icon': 'http://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Banana-Single.jpg/220px-Banana-Single.jpg'}, 
            'orange':{'icon': 'http://freeimagesarchive.com/data/media/38/7_orange.jpg'},
            'kiwi':{'icon': 'http://1.bp.blogspot.com/-XK8RbZ1MFz8/T88vJy9THfI/AAAAAAAABts/FWCuZptW_d0/s1600/kiwi+fruit.jpg'},
            'grape':{'icon': 'http://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Table_grapes_on_white.jpg/220px-Table_grapes_on_white.jpg'}}

        

class LogLlum(webapp2.RequestHandler):

    def install_contexts(self, um):
        try:
            reslist = um.ask(context=['Apps','Logging'])
            return
        except:
            pass

        context = ['Apps']
        ctx_obj = personis.Context(Identifier="Logging",
                  Description="The logging app",
                  perms={'ask':True, 'tell':True,
                  "resolvers": ["all","last10","last1","goal"]},
                  resolver=None, objectType="Context")
        print "Creating logging context "
        um.mkcontext(context,ctx_obj)
        context.append('Logging')

        cobj = personis.Component(Identifier="logged_items", component_type="activity", value_type="enum", 
                                       value_list=[i for i in item_list.keys()], resolver=None ,Description="All the items logged")
        um.mkcomponent(context=context, componentobj=cobj)

    def do_login(self):
        session = get_current_session()
        oauthconf = self.app.config.get('oauthconf')
        flow = OAuth2WebServerFlow(client_id=oauthconf['client_id'],
                        client_secret=oauthconf['client_secret'],
                        scope='https://www.personis.info/auth/model',
                        user_agent='Log-llum/1.0',
                        auth_uri=oauthconf['personis_uri']+'/authorize',
                        token_uri=oauthconf['personis_uri']+'/request_token')
        callback = oauthconf['callback']
        authorize_url = flow.step1_get_authorize_url(callback)
        session['flow'] = pickle.dumps(flow)
        return self.redirect(authorize_url)


    def authorized(self):
        session = get_current_session()
        if not 'code' in self.request.params:
            self.abort(400, detail='no code param')

        code = self.request.params['code']
        #logging.info('code: '+code)
        flow = session.get('flow')
        flow = pickle.loads(flow)
        if not flow:
            raise IOError()
        #p = httplib2.ProxyInfo(proxy_type=httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL, proxy_host='www-cache.it.usyd.edu.au', proxy_port=8000)
        #h = httplib2.Http(proxy_info=p)
        credentials = flow.step2_exchange(self.request.params)
        #ht = httplib2.Http(proxy_info=p)
        oauthconf = self.app.config.get('oauthconf')
        c = personis.Connection(uri = oauthconf['personis_uri'], credentials = credentials)
        session['connection'] = pickle.dumps(c)
        um = personis.Access(connection=c, debug=0)
        self.install_contexts(um)
        self.redirect('/')

    def log_me(self):
        session = get_current_session()
        if session.get('connection') == None:
            self.abort(400, detail='Log in first.')
        connection = pickle.loads(session.get('connection'))
        um = personis.Access(connection=connection, test=False)
        item = self.request.get('item')
        ev = personis.Evidence(source='llum-log', evidence_type="explicit", value=item, time=time.time())
        um.tell(context=['Apps','Logging'], componentid='logged_items', evidence=ev)
        return self.redirect('/')

    def get(self):
        session = get_current_session()
        if session.get('connection') == None:
            return self.redirect('/do_login')
        connection = pickle.loads(session.get('connection'))
        um = personis.Access(connection=connection, test=False)
        try:
            reslist = um.ask(context=["Personal"],view=['firstname', 'picture'])
        except AccessTokenRefreshError as e:
            print e
            return self.redirect('do_login')

        args = {'firstname': reslist[0].value, 'user_icon':reslist[1].value }
        i = 0
        for k,v in item_list.items():
            args[`i`+'name'] = k
            args[`i`+'pic'] = v['icon']
            i = i + 1

        self.response.write('''<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Logger</title>
        <link rel="shortcut icon" href="/favicon.ico" />
        <link rel="stylesheet" href="http://code.jquery.com/mobile/1.1.0/jquery.mobile-1.1.0.min.css" />
        <script src="http://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js">
        </script>
        <script src="http://code.jquery.com/mobile/1.1.0/jquery.mobile-1.1.0.min.js">
        </script>
    </head>
    <body id="home-index-action" class="ot">
        <div id="homePage" data-role="page" data-theme="o" class="homeBody">
        <div class="mainContentPanel" data-role="content">
        <div id="OTHomeLogo">Hi {0[firstname]}, <img src="{0[user_icon]}" style='max-width:50px; max-height:50px' border="0" class="homeLogo">. Log something!</div>
        <div class="ui-grid-b">
            <div class="ui-block-a">
                <a class="wrapper" href="/log_me?item={0[0name]}" id="ByName"><img style='max-width:100px; max-height:100px' src='{0[0pic]}'/></a>
            </div><!-- /grid-b -->
            <div class="ui-block-a">
                <a class="wrapper" href="/log_me?item={0[1name]}" id="ByName"><img style='max-width:100px; max-height:100px' src='{0[1pic]}'/></a>
            </div><!-- /grid-b -->
            <div class="ui-block-a">
                <a class="wrapper" href="/log_me?item={0[2name]}" id="ByName"><img style='max-width:100px; max-height:100px' src='{0[2pic]}'/></a>
            </div><!-- /grid-b -->
            <div class="ui-block-a">
                <a class="wrapper" href="/log_me?item={0[3name]}" id="ByName"><img style='max-width:100px; max-height:100px' src='{0[3pic]}'/></a>
            </div><!-- /grid-b -->
            <div class="ui-block-a">
                <a class="wrapper" href="/log_me?item={0[4name]}" id="ByName"><img style='max-width:100px; max-height:100px' src='{0[4pic]}'/></a>
            </div><!-- /grid-b -->
            <div class="ui-block-a">
                <a class="wrapper" href="/log_me?item={0[5name]}" id="ByName"><img style='max-width:100px; max-height:100px' src='{0[5pic]}'/></a>
            </div><!-- /grid-b -->
        </div>
        </div>
        </div>
        </body>
        </html>
        '''.format(args))


httplib2.debuglevel=0
logging.basicConfig(level=logging.INFO)
config = {}
config['oauthconf'] = yaml.load(file('oauth.ae.yaml','r'))
#config['webapp2_extras.sessions'] = {'secret_key': '0srag7dr89at7t034hjt'}
app = webapp2.WSGIApplication([
        webapp2.Route(r'/do_login', handler=LogLlum, handler_method='do_login'),
        webapp2.Route(r'/authorized', handler=LogLlum, handler_method='authorized'),
        webapp2.Route(r'/log_me', handler=LogLlum, handler_method='log_me'),
        (r'/', LogLlum)
    ],
    debug=False, config=config)



