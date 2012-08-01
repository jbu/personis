import os, sys

import httplib, oauth2
from optparse import OptionParser
import httplib2

from oauth2client.file import Storage
from oauth2client.client import Storage, Credentials, OAuth2WebServerFlow
from oauth2client.tools import run

import cherrypy
import wsgiref.handlers
import ConfigParser

from personis import client
import yaml
import time

item_list = {'apple':{'icon':'http://appleadayproject.files.wordpress.com/2011/03/apple-full2.jpg'},
            'pear':{'icon': 'http://4.bp.blogspot.com/-IgzE0L2YSdg/T1Pg-z8t6-I/AAAAAAAAAhU/cWfds0ulbLI/s1600/Pear.jpg'}, 
            'banana':{'icon': 'http://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Banana-Single.jpg/220px-Banana-Single.jpg'}, 
            'orange':{'icon': 'http://freeimagesarchive.com/data/media/38/7_orange.jpg'},
            'kiwi':{'icon': 'http://1.bp.blogspot.com/-XK8RbZ1MFz8/T88vJy9THfI/AAAAAAAABts/FWCuZptW_d0/s1600/kiwi+fruit.jpg'},
            'grape':{'icon': 'http://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Table_grapes_on_white.jpg/220px-Table_grapes_on_white.jpg'}}

class LogLlum(object):

    def __init__(self, oauthconf):
        self.oauthconf = yaml.load(file(oauthconf,'r'))

    @cherrypy.expose
    def do_login(self):
        flow = OAuth2WebServerFlow(client_id=self.oauthconf['client_id'],
                        client_secret=self.oauthconf['client_secret'],
                        scope='https://www.personis.info/auth/model',
                        user_agent='Log-llum/1.0',
                        auth_uri=self.oauthconf['personis_uri']+'/authorize',
                        token_uri=self.oauthconf['personis_uri']+'/request_token')
        callback = self.oauthconf['callback']
        authorize_url = flow.step1_get_authorize_url(callback)
        cherrypy.session['flow'] = flow
        raise cherrypy.HTTPRedirect(authorize_url)

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

    @cherrypy.expose
    def authorized(self, code, state=None):
        flow = cherrypy.session.get('flow')
        if not flow:
            raise IOError()
        p = httplib2.ProxyInfo(proxy_type=httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL, proxy_host='www-cache.it.usyd.edu.au', proxy_port=8000)
        h = httplib2.Http(proxy_info=p)
        credentials = flow.step2_exchange(cherrypy.request.params, h)
        ht = httplib2.Http(proxy_info=p)
        um = client.Access(uri = self.oauthconf['personis_uri'], credentials = credentials, http = ht)
        self.install_contexts(um)
        cherrypy.session['um'] = um
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def log_me(self, item):
        if cherrypy.session.get('um') == None:
            raise cherrypy.HTTPError(400, 'Log in first.')
        um = cherrypy.session.get('um')
        ev = client.Evidence(source='llum-log', evidence_type="explicit", value=item, time=time.time())
        um.tell(context=['Apps','Logging'], componentid='logged_items', evidence=ev)
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def index(self):
        if cherrypy.session.get('um') == None:
            raise cherrypy.HTTPRedirect('/do_login')
        um = cherrypy.session.get('um')
        reslist = um.ask(context=["Personal"],view=['firstname', 'picture'])

        ret = '''<!DOCTYPE html>
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
        '''.format({'firstname': reslist[0].value, 'user_icon':reslist[1].value })
        for k, v in item_list.items():
            ret = ret + '''<div class="ui-block-a">
                <a class="wrapper" href="/log_me?item={0[name]}" id="ByName"><img style='max-width:100px; max-height:100px' src='{0[pic]}'/></a>
            </div>
            '''.format({'name': k, 'pic': v['icon']})
        ret = ret + '</div></div></div></body></html>'
        return ret

if __name__ == '__main__':
    httplib2.debuglevel=0
    parser = OptionParser()
    parser.add_option("-o", "--oauthconf",
          dest="oauthconf", metavar='FILE',
          help="Oauth Config file", default='oauth.yaml')
    (options, args) = parser.parse_args()
    cherrypy.quickstart(LogLlum(options.oauthconf),'/',config='global.conf')
    cherrypy.engine.start()
    cherrypy.engine.block()

