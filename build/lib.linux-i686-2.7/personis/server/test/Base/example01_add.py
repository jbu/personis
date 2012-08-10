#!/usr/bin/env python

import unittest
import Personis_base
import os
import shutil
import sys

class TestPersonisBaseAdd(unittest.TestCase):

    def setUp(self):
        # create model
        shutil.copytree('models', 'testmodels')

    def tearDown(self):
        shutil.rmtree('testmodels')

    def test_add(self):
        um = Personis_base.Access(model="Alice", modeldir='testmodels', user='alice', password='secret')
        # create a piece of evidence with Alice as value
        ev = Personis_base.Evidence(evidence_type="explicit", value="Alice")
        # tell this as user alice's first name
        um.tell(context=["Personal"], componentid='firstname', evidence=ev)
        ev = Personis_base.Evidence(evidence_type="explicit", value="Smith")
        um.tell(context=["Personal"], componentid='lastname', evidence=ev)
        ev = Personis_base.Evidence(evidence_type="explicit", value="female")
        um.tell(context=["Personal"], componentid='gender', evidence=ev)

        reslist = um.ask(context=["Personal"], view='fullname', resolver={'evidence_filter':"last1"})
        self.assertEqual(reslist[0].value, 'Alice')
        reslist = um.ask(context=["Personal"], view=['gender'], resolver={'evidence_filter':"last1"})
        self.assertEqual(reslist[0].value, 'female')

if __name__ == '__main__':
    unittest.main()
