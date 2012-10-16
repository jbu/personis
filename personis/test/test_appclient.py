#!/usr/bin/env python

import unittest
from personis import client, app_client
import os
import sys
import json
import httplib2
import time
import logging
#from Personis_util import printcomplist

class TestPersonis(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.ERROR)
 
        client_secrets = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'client_secrets.json')
        cls.server_uri = json.loads(open(client_secrets,'r').read())['installed']['token_uri'][:-len('request_token')]
        
        #p = httplib2.ProxyInfo(proxy_type=httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL, proxy_host='www-cache.it.usyd.edu.au', proxy_port=8000)
        p = None
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
        cls.um.delcontext(context=["test"])

    def test_connect(self):
        appdetails = self.um.registerapp(app="MyHealth", desc="My Health Manager", password="pass9")
        self.assertEqual(appdetails['description'], u'My Health Manager')
        apps = self.um.listapps()
        self.assertIn(u'MyHealth', apps.keys())

        self.um.setpermission(context=["test"], app="MyHealth", permissions={'ask':True, 'tell':False})

        perms = self.um.getpermission(context=["test"], app="MyHealth")
        self.assertEquals(perms, {'ask': True, 'tell': False})

        cli = app_client.Model(self.server_uri, model='jamesuther', app='MyHealth', password='pass9')

        # create a piece of evidence with Alice as value
        ev = client.Evidence(evidence_type="explicit", value="Alice")
        # tell this as user alice's first name
        self.um.tell(context=["test"], componentid='firstname', evidence=ev)
        res = cli.ask(context=["test"], view=['firstname'])
        self.assertEqual(res[0].value, u'Alice')

        self.um.deleteapp(app="MyHealth")

        apps = self.um.listapps()
        self.assertNotIn(u'MyHealth', apps)

        with self.assertRaises(Exception) as e:
            res = cli.ask(context=["test"], view=['firstname'])


if __name__ == '__main__':
    unittest.main()