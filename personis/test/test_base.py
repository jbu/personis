#!/usr/bin/env python

import unittest
import json
from personis.server import base, mkmodel
from personis import client
import os
import shutil
import sys
import logging
import tempfile

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
        #shutil.rmtree('models')
        pass

    def test_ask_firstname(self):
        res = self.um.ask(context=["Personal"], view=['firstname'])
        self.assertEqual(res[0].value, u'Alice')

    def test_ask_gender(self):
        res = self.um.ask(context=["Personal"], view=['gender'], resolver={'evidence_filter':"last1"})
        self.assertEqual(res[0].value, u'female')

    def test_ask_fullname(self):
        res = self.um.ask(context=["Personal"], view='fullname')
        self.assertEqual(res[0].value, u'Alice')
        self.assertEqual(res[1].value, u'Smith')

    def test_ask_fullname_resolver(self):
        res = self.um.ask(context=["Personal"], view='fullname', resolver={'evidence_filter':"last1"})
        self.assertEqual(res[0].value, u'Alice')
        self.assertEqual(res[1].value, u'Smith')

    def test_ask_comboview(self):
        res = self.um.ask(context=["Personal"], view=['firstname', 'lastname'])
        self.assertEqual(res[0].value, u'Alice')
        self.assertEqual(res[1].value, u'Smith')

    def test_make_age(self):
        cobj = base.Component(Identifier="age", component_type="attribute", Description="age", goals=[['Personal', 'Health', 'weight']], value_type="number")
        res = self.um.mkcomponent(context=["Personal"], componentobj=cobj)

        ev = base.Evidence(evidence_type="explicit", value=17)
        self.um.tell(context=["Personal"], componentid='age', evidence=ev)
        reslist = self.um.ask(context=["Personal"], view=['age'], resolver={'evidence_filter':"all"})

        self.assertEqual(reslist[0].value, 17)

    def test_del_age(self):
        self.um.delcomponent(context=["Personal"], componentid = "age")

        info = self.um.ask(context=["Personal"], showcontexts=True)
        (cobjlist, contexts, theviews, thesubs) = info
        self.assertNotIn(u'age', cobjlist)

    def test_mk_context(self):
        cobj = client.Context(Identifier='test', Description='a test component')
        t = self.um.mkcontext(context=['Personal'], contextobj=cobj)
        self.assertEqual(t, True)

        info = self.um.ask(context=["Personal"], showcontexts=True)
        (cobjlist, contexts, theviews, thesubs) = info
        self.assertIn(u'test', contexts)

    def test_del_context(self):
        self.um.delcontext(context=["Personal",'test'])

        info = self.um.ask(context=["Personal"], showcontexts=True)
        (cobjlist, contexts, theviews, thesubs) = info
        self.assertNotIn(u'test', contexts)

    def test_mk_view(self):
        vobj = client.View(Identifier="email_details", component_list=["firstname", "lastname", "email"])
        self.um.mkview(context=["Personal"], viewobj=vobj)
        reslist= self.um.ask(context=["Personal"], view = 'email_details', resolver={'evidence_filter':"all"})

        r2 = [u'firstname', u'lastname', u'email']
        r3 = [i.Identifier for i in reslist]

        self.assertItemsEqual(r2, r3)

    def test_rm_view(self):
        self.um.delview(context=['Personal'], viewid='email_details')
        info = self.um.ask(context=["Personal"], showcontexts=True)
        (cobjlist, contexts, theviews, thesubs) = info
        self.assertNotIn(u'email_details', theviews)


    def test_register_app(self):
        appdetails = self.um.registerapp(app="MyHealth", desc="My Health Manager", password="pass9")
        self.assertEqual(appdetails, {'password': 'c28cce9cbd2daf76f10eb54478bb0454', 'description': 'My Health Manager'})
        apps = self.um.listapps()
        self.assertEquals([u'MyHealth'], apps.keys())

        self.um.setpermission(context=["Personal"], app="MyHealth", permissions={'ask':True, 'tell':False})

        perms = self.um.getpermission(context=["Personal"], app="MyHealth")
        self.assertEquals(perms, {'ask': True, 'tell': False})

        with self.assertRaises(Exception) as e:
            perms = self.um.getpermission(context=["Personal"], app="withings")

        self.um.deleteapp(app="MyHealth")

        apps = self.um.listapps()
        self.assertEqual(apps, {})

    def test_export(self):
        m = self.um.export_model(context=['Personal'],
            resolver={'evidence_filter': 'all'},
            level=None)
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

        reslist = self.um.ask(context=['test-import', "Personal"], view='fullname')

        r = [r.value for r in reslist]
        rc = [u'Alice',u'Smith']
        self.assertItemsEqual(r, rc)

    def test_resolver(self):
        def myresolver(model=None, component=None, context=None, resolver_args=None):
            """     new resolver function 
            """
            if resolver_args == None:
                ev_filter = None
            else:
                ev_filter = resolver_args.get('evidence_filter')
            component.evidencelist = component.filterevidence(model=model, context=context, resolver_args=resolver_args)
            if len(component.evidencelist) > 0:
                component.value = component.evidencelist[-1]['value']
            return component

        self.um.resolverlist["myresolver"] = myresolver

        reslist = self.um.ask(context=["Personal"], view='fullname', resolver={"resolver":"myresolver", "evidence_filter":"all"})

        r = [r.value for r in reslist]
        rc = [u'Alice',u'Smith']

        self.assertItemsEqual(r, rc)

if __name__ == '__main__':
    unittest.main()