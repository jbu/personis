#!/usr/bin/env python

import unittest
import Personis_base
import os
import shutil
import sys
from Personis_util import printcomplist

class TestPersonisBaseAdd(unittest.TestCase):

    def setUp(self):
        # create model
        shutil.copytree('models', 'testmodels')
        self.um = Personis_base.Access(model="Alice", modeldir='testmodels', user='alice', password='secret')
        # create a piece of evidence with Alice as value
        ev = Personis_base.Evidence(evidence_type="explicit", value="Alice")
        # tell this as user alice's first name
        self.um.tell(context=["Personal"], componentid='firstname', evidence=ev)

        ev = Personis_base.Evidence(evidence_type="explicit", value="Smith")
        self.um.tell(context=["Personal"], componentid='lastname', evidence=ev)
        ev = Personis_base.Evidence(evidence_type="explicit", value="female")
        self.um.tell(context=["Personal"], componentid='gender', evidence=ev)

    def tearDown(self):
        shutil.rmtree('testmodels')

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
