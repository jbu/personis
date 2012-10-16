#!/usr/bin/env python

import unittest
from personis.server import server
from personis import client
import os
import shutil
import sys
from apiclient.http import HttpMockSequence
from multiprocessing import Process, Queue

from oauth2client.file import Storage
from oauth2client.client import Credentials
import json
import time
import logging
import httplib2
import logging
import tempfile
#from Personis_util import printcomplist

class TestPersonisBaseAdd(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.ERROR)
        #if os.path.exists('models'):
            #shutil.rmtree('models')
        #shutil.copytree('testmodels', 'models')
        #cls.stopq = Queue()

        #cls.serverp = Process(target=server.runServer, args=('models', 'server-test.conf', 'admins-test.yaml', 'oauth-clients-test.json', 'oauth_access_tokens.dat', logging.DEBUG, cls.stopq, 'client_secrets_google.json'))
        #cls.serverp.start()
        #cls.stopq.put('test')

        #time.sleep(1)

        client_secrets = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secrets.json')
        p = None # httplib2.ProxyInfo(proxy_type=httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL, proxy_host='www-cache.it.usyd.edu.au', proxy_port=8000)
        cls.um = client.util.LoginFromClientSecrets(filename=client_secrets, 
            http=httplib2.Http(proxy_info=p, disable_ssl_certificate_validation=True), 
            credentials='server_test_cred.dat')
        cobj = client.Context(Identifier='test', Description='a test component')
        t = cls.um.mkcontext(context=[''], contextobj=cobj)
        cobj = client.Component(Identifier="firstname", component_type="attribute", Description="First name", value_type="string")
        res = cls.um.mkcomponent(context=["test"], componentobj=cobj)
        cobj = client.Component(Identifier="lastname", component_type="attribute", Description="Last name", value_type="string")
        res = cls.um.mkcomponent(context=["test"], componentobj=cobj)
        cobj = client.Component(Identifier="gender", component_type="attribute", Description="Gender", value_type="enum", value_list=['male','female'])
        res = cls.um.mkcomponent(context=["test"], componentobj=cobj)
        cobj = client.Component(Identifier="email", component_type="attribute", Description="email address", value_type="string")
        res = cls.um.mkcomponent(context=["test"], componentobj=cobj)

        vobj = client.View(Identifier="fullname", component_list=["firstname", "lastname"])
        cls.um.mkview(context=["test"], viewobj=vobj)

    @classmethod
    def tearDownClass(cls):
        #cls.stopq.put('exit')
        #print 'here1'
        #cls.serverp.join()
        #print 'here2' 
        #shutil.rmtree('models')
        cls.um.delcontext(context=["test"])

    def test_ask_tell(self):
        # create a piece of evidence with Alice as value
        ev = client.Evidence(evidence_type="explicit", value="Alice")
        # tell this as user alice's first name
        self.um.tell(context=["test"], componentid='firstname', evidence=ev)
        res = self.um.ask(context=["test"], view=['firstname'])
        self.assertEqual(res[0].value, u'Alice')

        ev = client.Evidence(evidence_type="explicit", value="Smith")
        self.um.tell(context=["test"], componentid='lastname', evidence=ev)
        ev = client.Evidence(evidence_type="explicit", value="female")
        self.um.tell(context=["test"], componentid='gender', evidence=ev)

        print(">>>> subscribe to changes in lastname")

        sub = """
<default!./test/lastname> ~ '.*' :
         NOTIFY 'http://www.it.usyd.edu.au/~bob/Personis/tst.cgi?' 'lastname=' <./test/lastname> """

         result = self.um.subscribe(context=["test"], view=['lastname'], subscription={'user':'alice', 'password':'qwert', 'statement':sub})
         print(result)

         print(">>>> add a subscription that is checked regularly according to a cron rule")
         # min, hour, day of month, month, day of week
         sub = """
 ["1-58 * * * *"] <default!./test/lastname> ~ '.*' :
         NOTIFY 'http://www.it.usyd.edu.au/~bob/Personis/tst.cgi?' 'lastname=' <./test/lastname> """
         result = um.subscribe(context=["test"], view=['lastname'], subscription={'user':'alice', 'password':'secret', 'statement':sub})
         print(result)

if __name__ == '__main__':
    unittest.main()