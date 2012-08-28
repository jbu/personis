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
from collections import OrderedDict


# items must be listed in correct order, so use OrderedDict and add manually.
item_list = OrderedDict()

item_list['fruit'] = {'category': 'food', 'icon':'/image/fruit.jpg'}
item_list['running'] = {'category': 'activity', 'icon': '/image/running.jpg'}
item_list['vegetables'] = {'category': 'food', 'icon': '/image/vegetables.jpg'}
item_list['walking'] = {'category': 'activity', 'icon': '/image/walking.jpg'}

        # running - http://www.flickr.com/photos/good_day/20723337/in/photostream/
        # walking - http://www.flickr.com/photos/o5com/5081595200/in/photostream/
        # fruit - http://www.flickr.com/photos/doug88888/2780642603/in/photostream/
        # vegetables - http://www.flickr.com/photos/suckamc/2488644619/in/photostream/


class LogLlum(webapp2.RequestHandler):


    def install_contexts(self, um):
        try:
            reslist = um.ask(context=['Apps','Logging'], view=['logged_items'])
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
        try:
            um.mkcontext(context,ctx_obj)
        except:
            logging.debug('already have logging context')
        context.append('Logging')

        value_list = [i for i in item_list.keys()] + [i+'-' for i in item_list.keys()]
        cobj = client.Component(Identifier="logged_items", component_type="activity", value_type="enum", 
                                       value_list=value_list, resolver=None ,Description="All the items logged")
        try:
            um.mkcomponent(context=context, componentobj=cobj)
        except:
            logging.debug('already have logged_items')

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
        credentials = flow.step2_exchange(self.request.params, http = httplib2.Http(disable_ssl_certificate_validation=True))
        oauthconf = self.app.config.get('oauthconf')
        c = client.Connection(uri = oauthconf['personis_uri'], credentials = credentials)
        session['connection'] = pickle.dumps(c)
        um = client.Access(connection=c, http = httplib2.Http(disable_ssl_certificate_validation=True))
        self.install_contexts(um)
        self.redirect('/')

    def log_me(self):
        if self.request.method != 'POST':
            self.abort(400, detail="POST only")
        session = get_current_session()
        if session.get('connection') == None:
            self.abort(400, detail='Log in first.')
        logging.debug('logme %s', self.request.get('item'))
        connection = pickle.loads(session.get('connection'))
        um = client.Access(connection=connection, http = httplib2.Http(disable_ssl_certificate_validation=True), test=False)
        item = self.request.get('item')
        ev = client.Evidence(source='llum-log', evidence_type="explicit", value=item, time=time.time())
        um.tell(context=['Apps','Logging'], componentid='logged_items', evidence=ev)
        self.response.write(item)

    def get(self):
        session = get_current_session()
        if session.get('connection') == None:
            logging.debug('no connection found. logging in')
            return self.redirect('/do_login')
        connection = pickle.loads(session.get('connection'))
        um = client.Access(connection=connection, test=False, http = httplib2.Http(disable_ssl_certificate_validation=True))
        self.install_contexts(um)
        try:
            reslist = um.ask(context=["Personal"],view=['firstname', 'picture'])
        except AccessTokenRefreshError as e:
            logging.info('access token refresh error %s', e)
            return self.redirect('/do_login')

        ret = '''
    <!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="stylesheet" href="https://ajax.aspnetcdn.com/ajax/jquery.mobile/1.1.1/jquery.mobile-1.1.1.min.css" />
        <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.8.0/jquery.min.js"></script>
        <script src="https://ajax.aspnetcdn.com/ajax/jquery.mobile/1.1.1/jquery.mobile-1.1.1.min.js"></script>
        <link rel="stylesheet" href="/static/my.css"/>
        <script src="/static/my.js"></script>
    </head>
    <body>
        <!-- Home -->
        <div data-role="page" id="page1">
            <div data-theme="a" data-role="header" data-position="fixed">
            <h3>My Health Logger</h3>
            <a href=""><img src='{0[user_icon]}' style="height: 50px"/></a>
            </div>
            <div data-role="content" style="padding: 15px">
                <div class="ui-grid-a">
                    <div class="ui-block-a" align="center"><h2>Food</h2></div>
                    <div class="ui-block-b" align="center"><h2>Activity</h2></div>'''.format({'user_icon':reslist[1].value })
        l = 'a'
        for k, v in item_list.items():
            ret = ret + ''' <div class="ui-block-{0[l]}">
                <div class="imageC">
                    <img class="wrapper"  src='{0[pic]}' alt='{0[name]}'/>
                </div>
            </div>'''.format({'l': l,'name': k.strip(), 'pic': v['icon']})
            l = 'a' if l == 'b' else 'b'
        ret = ret + ''' 
                </div>
                <button id="undo">Undo</button>
            <div data-role="collapsible" data-collapsed="false" id="coll" data-theme='c' data-content-theme="c">
              <h3>Logged items</h3>
                <p class='loggedItem'></p>
            </div>
        </div>
        </div>
    </body>
</html>'''
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



