#!/usr/bin/env python

import unittest
from personis import client, server
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
#from Personis_util import printcomplist

class TestPersonisBaseAdd(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.INFO)
        if os.path.exists('models'):
            shutil.rmtree('models')
        shutil.copytree('testmodels', 'models')
        cls.stopq = Queue()

        cls.serverp = Process(target=server.server.runServer, args=('models', 'server-test.conf', 'admins-test.yaml', 
            'oauth-clients-test.json', 'oauth_access_tokens.dat', logging.DEBUG, cls.stopq, 'client_secrets_google.json'))
        cls.serverp.start()
        cls.stopq.put('test')

        time.sleep(1)

        storage = Storage('credentials.dat')
        credentials = storage.get()
        cjson = json.loads(credentials.to_json())
        h = httplib2.Http(proxy_info=None)
        cls.um = client.Access(uri = 'http://127.0.0.1:2005/', 
            credentials = credentials, http=h)
        # create a piece of evidence with Alice as value
        ev = client.Evidence(evidence_type="explicit", value="Alice")
        # tell this as user alice's first name
        cls.um.tell(context=["Personal"], componentid='firstname', evidence=ev)

        ev = client.Evidence(evidence_type="explicit", value="Smith")
        cls.um.tell(context=["Personal"], componentid='lastname', evidence=ev)
        ev = client.Evidence(evidence_type="explicit", value="female")
        cls.um.tell(context=["Personal"], componentid='gender', evidence=ev)

    @classmethod
    def tearDownClass(cls):
        cls.stopq.put('exit')
        print 'here1'
        cls.serverp.join()
        print 'here2'
        shutil.rmtree('models')

    def test_ask_firstname(self):
        res = self.um.ask(context=["Personal"], view=['firstname'])
        self.assertEqual(res[0].value, 'Alice')

    def test_ask_gender(self):
        res = self.um.ask(context=["Personal"], view=['gender'], resolver={'evidence_filter':"last1"})
        self.assertEqual(res[0].value, 'female')

    def test_ask_fullname(self):
        res = self.um.ask(context=["Personal"], view='fullname')
        self.assertEqual(res[0].value, 'Alice')
        self.assertEqual(res[1].value, 'Smith')

    def test_ask_fullname_resolver(self):
        res = self.um.ask(context=["Personal"], view='fullname', resolver={'evidence_filter':"last1"})
        self.assertEqual(res[0].value, 'Alice')
        self.assertEqual(res[1].value, 'Smith')

    def test_ask_comboview(self):
        res = self.um.ask(context=["Personal"], view=['firstname', 'lastname'])
        self.assertEqual(res[0].value, 'Alice')
        self.assertEqual(res[1].value, 'Smith')

if __name__ == '__main__':
    unittest.main()
