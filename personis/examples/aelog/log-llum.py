import os, sys

from oauth2client.file import Storage
from oauth2client.client import Storage, Credentials, OAuth2WebServerFlow, AccessTokenRefreshError
from oauth2client.tools import run

import httplib
import httplib2
import webapp2
from gaesessions import get_current_session

from personis import client
import yaml
import time
import logging
import pickle

item_list = {'fruit':{'icon':'http://2.bp.blogspot.com/-jDaZn2jh-8g/T_nBaiND65I/AAAAAAAAEEU/xfTEI7jn9WA/s400/800px-Culinary_fruits_front_view.jpg'},
            'vegetables':{'icon': 'http://vegansolution.files.wordpress.com/2009/11/nutrition.jpg?w=500'}, 
            'running':{'icon': 'http://media.tumblr.com/tumblr_lr1zbqDTYY1qbjt03.jpg'},
            'walking':{'icon': 'http://www.thenordicwalking.com/wp-content/uploads/2011/02/nw123.jpg'}, 
            }

        

class LogLlum(webapp2.RequestHandler):

    def install_contexts(self, um):
        try:
            reslist = um.ask(context=['Apps','Logging'])
            return
        except:
            pass

        context = ['Apps']
        ctx_obj = client.Context(Identifier="Logging",
                  Description="The logging app",
                  perms={'ask':True, 'tell':True,
                  "resolvers": ["all","last10","last1","goal"]},
                  resolver=None, objectType="Context")
        print "Creating logging context "
        um.mkcontext(context,ctx_obj)
        context.append('Logging')

        cobj = client.Component(Identifier="logged_items", component_type="activity", value_type="enum", 
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
        flow = session.get('flow')
        flow = pickle.loads(flow)
        if not flow:
            raise IOError()
        session['flow'] = None
        credentials = flow.step2_exchange(self.request.params, httplib2.Http(disable_ssl_certificate_validation=True))
        oauthconf = self.app.config.get('oauthconf')
        c = client.Connection(uri = oauthconf['personis_uri'], credentials = credentials, http=httplib2.Http(disable_ssl_certificate_validation=True))
        session['connection'] = pickle.dumps(c)
        um = client.Access(connection=c)
        self.install_contexts(um)
        self.redirect('/')

    def log_me(self):
        session = get_current_session()
        if session.get('connection') == None:
            self.abort(400, detail='Log in first.')
        connection = pickle.loads(session.get('connection'))
        um = client.Access(connection=connection, test=False)
        item = self.request.get('item')
        ev = client.Evidence(source='llum-log', evidence_type="explicit", value=item, time=time.time())
        um.tell(context=['Apps','Logging'], componentid='logged_items', evidence=ev)
        return self.redirect('/')

    def get(self):
        session = get_current_session()
        if session.get('connection') == None:
            logging.debug('no connection found. logging in')
            return self.redirect('/do_login')
        connection = pickle.loads(session.get('connection'))
        um = client.Access(connection=connection, test=False)
        try:
            reslist = um.ask(context=["Personal"],view=['firstname', 'picture'])
        except AccessTokenRefreshError as e:
            logging.info('access token refresh error '+e)
            return self.redirect('/do_login')

        ret = '''
<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>
        </title>
        <link rel="stylesheet" href="https://ajax.aspnetcdn.com/ajax/jquery.mobile/1.1.0/jquery.mobile-1.1.0.min.css" />
        <link rel="stylesheet" href="my.css" />
        <style>
            /* App custom styles */
        </style>
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.7.1/jquery.min.js">
        </script>
        <script src="https://ajax.aspnetcdn.com/ajax/jquery.mobile/1.1.0/jquery.mobile-1.1.0.min.js">
        </script>
        <script src="my.js">
        </script>
    </head>
    <body>
        <!-- Home -->
        <div data-role="page" id="page1">
            <div data-theme="a" data-role="header" data-position="fixed">
                <h3>
                    My Health Logger
                </h3>
            </div>
            <div data-role="content" style="padding: 15px">

                <div class="ui-grid-a">
                    <div class="ui-block-a" align="center">
                        <h2>
                            Food
                        </h2>
                    </div>
                    <div class="ui-block-b" align="center">
                        <h2>
                            Activity
                        </h2>
                    </div>
        '''
        l = 'a'
        for k, v in item_list.items():
            ret = ret + '''<div class="ui-block-{0[l]}">
                    <div style=" text-align:center; padding: 5px">
                        <a class="wrapper" href="/log_me?item={0[name]}" id="ByName"><img style='width:100%; ' src='{0[pic]}'/></a>
                    </div>
                </div>
            '''.format({'l': l,'name': k, 'pic': v['icon']})
            l = 'a' if l == 'b' else 'b'
        ret = ret + '''
                    
                </div>
                <div data-role="collapsible-set" data-theme="" data-content-theme="">
                    <div data-role="collapsible" data-collapsed="false">
                        <h3>
                            Activity
                        </h3>
                    </div>
                </div>
                <a data-role="button" data-transition="fade" href="#page1">
                    Undo
                </a>
            </div>
        </div>
        <script>
            //App custom javascript
        </script>
    </body>
</html>
        '''
        self.response.write(ret)


httplib2.debuglevel=5
logging.basicConfig(level=logging.DEBUG)
config = {}
config['oauthconf'] = yaml.load(file('oauth.ae.yaml','r'))

app = webapp2.WSGIApplication([
        webapp2.Route(r'/do_login', handler=LogLlum, handler_method='do_login'),
        webapp2.Route(r'/authorized', handler=LogLlum, handler_method='authorized'),
        webapp2.Route(r'/log_me', handler=LogLlum, handler_method='log_me'),
        (r'/', LogLlum)
    ],
    debug=False, config=config)



