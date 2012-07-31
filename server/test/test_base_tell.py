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

    def tearDown(self):
        shutil.rmtree('testmodels')

    def test_tell(self):
        # create a piece of evidence with Alice as value
        ev = Personis_base.Evidence(evidence_type="explicit", value="Alice")
        # tell this as user alice's first name
        self.um.tell(context=["Personal"], componentid='firstname', evidence=ev)

        ev = Personis_base.Evidence(evidence_type="explicit", value="Smith")
        self.um.tell(context=["Personal"], componentid='lastname', evidence=ev)
        ev = Personis_base.Evidence(evidence_type="explicit", value="female")
        self.um.tell(context=["Personal"], componentid='gender', evidence=ev)



if __name__ == '__main__':
    unittest.main()
