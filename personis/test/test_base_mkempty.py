#!/usr/bin/env python

import unittest
from personis.server import base, mkmodel
import os
import shutil
import sys

class TestPersonisBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if os.path.exists('models'):
            shutil.rmtree('models')
        os.mkdir('models')

        mkmodel.mkmodel(model='alice', mfile='empty.prod.mdef', modeldir='models', user='alice')
        um = base.Access(model="alice", modeldir='models', user='alice')
        ev = base.Evidence(evidence_type="explicit", value="test")
        um.tell(context=["Admin", 'modelinfo'], componentid='personisversion', evidence=ev)


    @classmethod
    def tearDownClass(cls):
        shutil.rmtree('models')

    def test_ask_modelversion(self):
        um = base.Access(model="alice", modeldir='models', user='alice')
        res = um.ask(context=["Admin", 'modelinfo'], view=['personisversion'])
        self.assertEqual(res[0].value, 'test')

if __name__ == '__main__':
    unittest.main()
