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
        p = httplib2.ProxyInfo(proxy_type=httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL, proxy_host='www-cache.it.usyd.edu.au', proxy_port=8000)
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


    def test_ask_fullname(self):
        ev = client.Evidence(evidence_type="explicit", value="Alice")
        # tell this as user alice's first name
        self.um.tell(context=["test"], componentid='firstname', evidence=ev)
        ev = client.Evidence(evidence_type="explicit", value="Smith")
        self.um.tell(context=["test"], componentid='lastname', evidence=ev)
        res = self.um.ask(context=["test"], view='fullname')

        self.assertEqual(res[0].value, u'Alice')
        self.assertEqual(res[1].value, u'Smith')

    def test_ask_fullname_resolver(self):
        ev = client.Evidence(evidence_type="explicit", value="Alice")
        # tell this as user alice's first name
        self.um.tell(context=["test"], componentid='firstname', evidence=ev)
        ev = client.Evidence(evidence_type="explicit", value="Smith")
        self.um.tell(context=["test"], componentid='lastname', evidence=ev)
        res = self.um.ask(context=["test"], view='fullname', resolver={'evidence_filter':"last1"})
        self.assertEqual(res[0].value, u'Alice')
        self.assertEqual(res[1].value, u'Smith')

    def test_ask_comboview(self):
        ev = client.Evidence(evidence_type="explicit", value="Alice")
        # tell this as user alice's first name
        self.um.tell(context=["test"], componentid='firstname', evidence=ev)
        ev = client.Evidence(evidence_type="explicit", value="Smith")
        self.um.tell(context=["test"], componentid='lastname', evidence=ev)
        res = self.um.ask(context=["test"], view=['firstname', 'lastname'])
        self.assertEqual(res[0].value, u'Alice')
        self.assertEqual(res[1].value, u'Smith')

    def test_make_del_age(self):
        cobj = client.Component(Identifier="age", component_type="attribute", Description="age", goals=[['Personal', 'Health', 'weight']], value_type="number")
        res = self.um.mkcomponent(context=["test"], componentobj=cobj)

        ev = client.Evidence(evidence_type="explicit", value=17)
        self.um.tell(context=["test"], componentid='age', evidence=ev)
        reslist = self.um.ask(context=["test"], view=['age'], resolver={'evidence_filter':"all"})

        self.assertEqual(reslist[0].value, 17)
        self.um.delcomponent(context=["test"], componentid = "age")

        info = self.um.ask(context=["test"], showcontexts=True)
        (cobjlist, contexts, theviews, thesubs) = info
        self.assertNotIn(u'age', cobjlist)

    def test_mk_del_view(self):
        vobj = client.View(Identifier="email_details", component_list=["firstname", "lastname", "email"])
        self.um.mkview(context=["test"], viewobj=vobj)
        reslist= self.um.ask(context=["test"], view = 'email_details', resolver={'evidence_filter':"all"})

        r2 = [u'firstname', u'lastname', u'email']
        r3 = [i.Identifier for i in reslist]

        self.assertItemsEqual(r2, r3)

        self.um.delview(context=['test'], viewid='email_details')
        info = self.um.ask(context=["test"], showcontexts=True)
        (cobjlist, contexts, theviews, thesubs) = info
        self.assertNotIn(u'email_details', theviews)

    def test_register_app(self):
        appdetails = self.um.registerapp(app="MyHealth", desc="My Health Manager", password="pass9")
        self.assertEqual(appdetails['description'], u'My Health Manager')
        apps = self.um.listapps()
        self.assertIn(u'MyHealth', apps.keys())

        self.um.setpermission(context=["test"], app="MyHealth", permissions={'ask':True, 'tell':False})

        perms = self.um.getpermission(context=["test"], app="MyHealth")
        self.assertEquals(perms, {'ask': True, 'tell': False})

        with self.assertRaises(Exception) as e:
            perms = self.um.getpermission(context=["test"], app="withings")

        self.um.deleteapp(app="MyHealth")

        apps = self.um.listapps()
        self.assertNotIn(u'MyHealth', apps)

    def test_export(self):
        ev = client.Evidence(evidence_type="explicit", value="Alice")
        # tell this as user alice's first name
        self.um.tell(context=["test"], componentid='firstname', evidence=ev)

        m = self.um.export_model(context=['test'],
            resolver={'evidence_filter': 'all'})
        tempfile_path = tempfile.mkstemp()[1]

        f  =open(tempfile_path,'w')
        f.write(m)
        f.close()

        cobj = client.Context(Identifier='test-import', Description='a test component')
        t = self.um.mkcontext(context=[], contextobj=cobj)

        modeljson = open(tempfile_path,'r').read()
        modeljson = json.loads(modeljson)
        self.assertEquals(modeljson['components']['firstname']['value'], 'Alice')
        self.um.import_model(context=['test-import'], partial_model=modeljson)

        reslist = self.um.ask(context=['test-import', 'test'], view='fullname')

        r = [r.value for r in reslist]
        rc = [u'Alice',u'Smith']
        self.assertItemsEqual(r, rc)

if __name__ == '__main__':
    unittest.main()