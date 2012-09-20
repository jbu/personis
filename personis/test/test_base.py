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

        mkmodel.mkmodel(model='alice', mfile='empty.prod.mdef', modeldir='models', user='alice')
        cls.um = base.Access(model="alice", modeldir='models', user='alice')
        # create a piece of evidence with Alice as value
        cobj = client.Context(Identifier='test', Description='a test component')
        t = cls.um.mkcontext(context=[''], contextobj=cobj)
        cobj = base.Component(Identifier="firstname", component_type="attribute", Description="First name", value_type="string")
        res = cls.um.mkcomponent(context=["test"], componentobj=cobj)
        cobj = base.Component(Identifier="lastname", component_type="attribute", Description="Last name", value_type="string")
        res = cls.um.mkcomponent(context=["test"], componentobj=cobj)
        cobj = base.Component(Identifier="gender", component_type="attribute", Description="Gender", value_type="enum", value_list=['male','female'])
        res = cls.um.mkcomponent(context=["test"], componentobj=cobj)
        cobj = base.Component(Identifier="email", component_type="attribute", Description="email address", value_type="string")
        res = cls.um.mkcomponent(context=["test"], componentobj=cobj)

        vobj = client.View(Identifier="fullname", component_list=["firstname", "lastname"])
        cls.um.mkview(context=["test"], viewobj=vobj)

    @classmethod
    def tearDownClass(cls):
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
        cobj = base.Component(Identifier="age", component_type="attribute", Description="age", goals=[['Personal', 'Health', 'weight']], value_type="number")
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

        ev = client.Evidence(evidence_type="explicit", value="Alice")
        self.um.tell(context=["test"], componentid='firstname', evidence=ev)
        ev = client.Evidence(evidence_type="explicit", value="Smith")
        reslist = self.um.ask(context=["test"], view='fullname', resolver={"resolver":"myresolver", "evidence_filter":"all"})

        r = [r.value for r in reslist]
        rc = [u'Alice',u'Smith']

        self.assertItemsEqual(r, rc)

    def test_register_app(self):
        appdetails = self.um.registerapp(app="MyHealth", desc="My Health Manager", password="pass9")
        self.assertEqual(appdetails, {u'realm': u'password', u'password': u'c28cce9cbd2daf76f10eb54478bb0454', u'givenpw': None, u'description': u'My Health Manager'})
        apps = self.um.listapps()
        self.assertIn(u'MyHealth', apps.keys())

        # registered app. should work
        appum = base.Access(model="alice", modeldir='models', user='MyHealth', password='pass9')
        # Ask for Alice's fullname as app 'MyHealth' (should NOT work)")
        with self.assertRaises(Exception) as e:
            reslist = appum.ask(context=["test"], view='fullname')

        self.um.setpermission(context=["test"], app="MyHealth", permissions={'ask':True, 'tell':False})
        perms = self.um.getpermission(context=["test"], app="MyHealth")
        self.assertEquals(perms, {'ask': True, 'tell': False})

        #should work now.
        reslist = appum.ask(context=["test"], view='fullname')
        #mainly checking it doesn't throw an execption, but should really assert a return value.

        #Now try and tell a new value for first name (should NOT work)
        with self.assertRaises(Exception) as e:
            ev = Personis_base.Evidence(evidence_type="explicit", value="Fred")
            appum.tell(context=["test"], componentid='firstname', evidence=ev)

        # registered app. should work
        um = base.Access(model="alice", modeldir='models', user='MyHealth', password='pass9')

        self.um.deleteapp(app="MyHealth")

        apps = self.um.listapps()
        self.assertNotIn(u'MyHealth', apps)

        # try and set permission on unregistered app
        with self.assertRaises(Exception) as e:
            self.um.setpermission(context=["test"], app="withings", permissions={'ask':True, 'tell':False})
        # try and get permission on ungrestiered app
        with self.assertRaises(Exception) as e:
            perms = self.um.getpermission(context=["test"], app="withings")
        # try access from unregistered app
        with self.assertRaises(Exception) as e:
            um = base.Access(model="alice", modeldir='models', user='withings')


if __name__ == '__main__':
    unittest.main()