#!/usr/bin/env python

import unittest
from personis.server import base, mkmodel
import os
import shutil
import sys
import logging

class TestPersonisBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.ERROR)
        if os.path.exists('models'):
            shutil.rmtree('models')
        os.mkdir('models')

        mkmodel.mkmodel(model='alice', mfile='user.mdef', modeldir='models', user='alice')
        cls.um = base.Access(model="alice", modeldir='models', user='alice')
        # create a piece of evidence with Alice as value
        ev = base.Evidence(evidence_type="explicit", value="Alice")
        # tell this as user alice's first name
        cls.um.tell(context=["Personal"], componentid='firstname', evidence=ev)

        ev = base.Evidence(evidence_type="explicit", value="Smith")
        cls.um.tell(context=["Personal"], componentid='lastname', evidence=ev)
        ev = base.Evidence(evidence_type="explicit", value="female")
        cls.um.tell(context=["Personal"], componentid='gender', evidence=ev)

    @classmethod
    def tearDownClass(cls):
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
