import os, sys

sys.path.insert(0, '/home/jbu/src/jbu-personis/Src')

import httplib, oauth2
from optparse import OptionParser
import httplib2

from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError, Storage, Credentials, OAuth2WebServerFlow
from oauth2client.tools import run

import cherrypy
import wsgiref.handlers
import ConfigParser

import Personis_server, Personis_base
import connection

class LogLlum(object):

    def do_login(self):
        flow = OAuth2WebServerFlow(client_id='2682957525366532517',
                                   client_secret='97984817434656507285',
                                   scope='https://www.personis.info/auth/model',
                                   user_agent='Log-llum/1.0',
                                   auth_uri='http://ec2-54-251-12-234.ap-southeast-1.compute.amazonaws.com:2005/authorize',
                                   token_uri='http://ec2-54-251-12-234.ap-southeast-1.compute.amazonaws.com:2005/request_token')
        callback = callback = 'http://enterprise.it.usyd.edu.au:8001/authorized'
        authorize_url = flow.step1_get_authorize_url(callback)

        cherrypy.session['flow'] = flow
        raise cherrypy.HTTPRedirect(authorize_url)

    @cherrypy.expose
    def authorized(self, code, state=None):
        flow = cherrypy.session.get('flow')
        if not flow:
            raise IOError()
        p = httplib2.ProxyInfo(proxy_type=httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL, proxy_host='www-cache.it.usyd.edu.au', proxy_port=8000)
        h = httplib2.Http(proxy_info=p)
        credentials = flow.step2_exchange(cherrypy.request.params, h)
        ht = httplib2.Http(proxy_info=p)
        c = connection.Connection(uri = 'http://ec2-54-251-12-234.ap-southeast-1.compute.amazonaws.com:2005/', credentials = credentials, http = ht)
        cherrypy.session['connection'] = c
        um = Personis_server.Access(connection=c, debug=True)

        ctx_obj = Personis_base.Context(Identifier="Apps",
                  Description="Applications available for use",
                  perms={'ask':True, 'tell':True,
                  "resolvers": ["all","last10","last1","goal"]},
                  resolver=None, objectType="Context")
        context = []
        context.append('.')
        print "Creating Applications context "
        um.mkcontext(context,ctx_obj)
        cherrypy.session['um'] = um
        raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def index(self):
        if cherrypy.session.get('um') == None:
            self.do_login()
        um = cherrypy.session.get('um')
        reslist = um.ask(context=["Personal"],view=['firstname'])
        username = reslist[0].value
        return '''
        <body>hello %s</body>
        '''%(username)

if __name__ == '__main__':
    httplib2.debuglevel=0
    cherrypy.quickstart(LogLlum(),'/',config='global.conf')
    cherrypy.engine.start()
    cherrypy.engine.block()

