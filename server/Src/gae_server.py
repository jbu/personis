#!/usr/bin/env python

#
# The Personis system is copyright 2000-2005 Personis Pty Ltd
#	Bob Kummerfeld 2005
#	bob@personis.oz.au
#
# Active User Models: added subscribe method to Access
#

import os, sys, httplib, traceback
from django.utils import simplejson as json
import jsoncall
import Personis_base
import Personis_a
import cPickle

import types

import webapp2
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class MainPage(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		self.response.headers['Content-Type'] = 'text/html'
		if user:  # signed in already
			self.response.out.write('Hello <em>%s</em>! [<a href="%s">sign out</a>]' % (
			user.nickname(), users.create_logout_url(self.request.uri)))
		else:     # let user choose authenticator
			self.response.out.write('Hello world! Sign in at: ')
			self.response.out.write('[<a href="%s">%s</a>]' % (
				users.create_login_url(self.request.uri), name))

app = webapp2.WSGIApplication([('/', MainPage)],
				debug=True)


def MkModel( model=None, modelserver=None, user=None, password=None, description=None, debug=0):
	if modelserver == None:
		raise ValueError, "modelserver is None"
	if ':' in modelserver:
		modelserver, modelport = modelserver.split(":")
	else:
		modelport = 2005 # default port for personis server
	modelname = model
	ok = False
	try:
		ok = jsoncall.do_call(modelserver, modelport, "mkmodel", {'modelname':modelname,\
									'descripion':description,\
									'user':user,\
									'password':password})
	except:
		if debug >0:
			traceback.print_exc()
		raise ValueError, "cannot create model '%s', server '%s'" % (modelname, modelserver)
	if not ok:
		raise ValueError, "server '%s' cannot create model '%s'" % (modelserver, modelname)



class Access(Personis_a.Access):
	""" 
	Client version of access for client/server system

	arguments:
		model		model name
		modelserver	model server and port
		user		user name
		password	password string
	returns a user model access object 
	"""
	def __init__(self, model=None, modelserver=None, user=None, password=None, debug=0):
		if modelserver == None:
			raise ValueError, "modelserver is None"
		if ':' in modelserver:
			self.modelserver, self.modelport = modelserver.split(":")
		else:
			self.modelserver = modelserver
			self.modelport = 2005 # default port for personis server
		self.modelname = model
		self.user = user
		self.password = password
		self.debug =debug
		ok = False
		try:
			if self.debug != 0:
				print "jsondocall:", self.modelserver, self.modelport, self.modelname, self.user, self.password
			ok = jsoncall.do_call(self.modelserver, self.modelport, "access", {'modelname':self.modelname,\
										'user':self.user,\
										'password':self.password})
			if self.debug != 0:
				print "---------------------- result returned", ok
		except:
			if debug >0:
				traceback.print_exc()
			raise ValueError, "cannot access model '%s', server '%s'" % (self.modelname, self.modelserver)
		if not ok:
			raise ValueError, "server '%s' cannot access model '%s'" % (self.modelserver, self.modelname)

	def ask(self,  
		context=[],
		view=None,
		resolver=None,
		showcontexts=None):
		"""
	arguments: (see Personis_base for details)
		context is a list giving the path of context identifiers
		view is either:
			an identifier of a view in the context specified
			a list of component identifiers or full path lists
			None indicating that the values of all components in
				the context be returned
		resolver specifies a resolver, default is the builtin resolver

	returns a list of component objects
		"""
		reslist = jsoncall.do_call(self.modelserver, self.modelport, "ask", {'modelname':self.modelname,\
										'user':self.user,\
										'password':self.password,\
										'context':context,\
										'view':view,\
										'resolver':resolver,\
										'showcontexts':showcontexts})
		complist = []
		if showcontexts:
			cobjlist, contexts, theviews, thesubs = reslist
			for c in cobjlist:
				comp = Personis_base.Component(**c)
				if c["evidencelist"]:
					comp.evidencelist = [Personis_base.Evidence(**e) for e in c["evidencelist"]]
				complist.append(comp)
			reslist = [complist, contexts, theviews, thesubs]
		else:
			for c in reslist:
				comp = Personis_base.Component(**c)
				if c["evidencelist"]:
					comp.evidencelist = [Personis_base.Evidence(**e) for e in c["evidencelist"]]
				complist.append(comp)
			reslist = complist
		return reslist
	
	def tell(self, 
		context=[],
		componentid=None,
		evidence=None):   # evidence obj
		"""
	arguments:
		context - a list giving the path to the required context
		componentid - identifier of the component
		evidence - evidence object to add to the component
		"""
		if componentid == None:
			raise ValueError, "tell: componentid is None"
		if evidence == None:
			raise ValueError, "tell: no evidence provided"
	
		return jsoncall.do_call(self.modelserver, self.modelport, "tell", {'modelname':self.modelname,\
										'user':self.user,\
										'password':self.password,\
										'context':context,\
										'componentid':componentid,\
										'evidence':evidence.__dict__})
	def mkcomponent(self,
		context=[],
		componentobj=None):
                """
        Make a new component in a given context
        arguments:
                context - a list giving the path to the required context
                componentobj - a Component object
        returns:
                None on success
                a string error message on error
                """
		if componentobj == None:
			raise ValueError, "mkcomponent: componentobj is None"
		return jsoncall.do_call(self.modelserver, self.modelport, "mkcomponent", {'modelname':self.modelname,\
										'user':self.user,\
                                                                                'password':self.password,\
                                                                                'context':context,\
                                                                                'componentobj':componentobj.__dict__})
	def delcomponent(self,
		context=[],
		componentid=None):
                """
        Delete an existing component in a given context
        arguments:
                context - a list giving the path to the required context
                id - the id for a componen
        returns:
                None on success
                a string error message on error
                """
		if componentid == None:
			raise ValueError, "delcomponent: componentid is None"
		return jsoncall.do_call(self.modelserver, self.modelport, "delcomponent", {'modelname':self.modelname,\
										'user':self.user,\
                                                                                'password':self.password,\
                                                                                'context':context,\
                                                                                'componentid':componentid})
	def delcontext(self,
		context=[]):
                """
        Delete an existing context
        arguments:
                context - a list giving the path to the required context
        returns:
                None on success
                a string error message on error
                """
		if context == None:
			raise ValueError, "delcontext: context is None"
		return jsoncall.do_call(self.modelserver, self.modelport, "delcontext", {'modelname':self.modelname,\
										'user':self.user,\
                                                                                'password':self.password,\
                                                                                'context':context})
	def getresolvers(self):
		'''Return a list of the available resolver names'''
		return jsoncall.do_call(self.modelserver, self.modelport, "getresolvers", {'modelname':self.modelname,\
										'user':self.user, 'password':self.password})
	
	def setresolver(self,
		context,
		componentid,
		resolver):
                """
        set the resolver for a given component in a given context
        arguments:
                context - a list giving the path to the required context
		componentid - the id for a given component
                resolver - the id of the resolver
        returns:
                None on success
                a string error message on error
                """
		if componentid == None:
			raise ValueError, "setresolver: componentid is None"
		return jsoncall.do_call(self.modelserver, self.modelport, "setresolver", {'modelname':self.modelname,\
										'user':self.user,\
                                                                                'password':self.password,\
                                                                                'context':context,\
                                                                                'componentid':componentid, \
										'resolver':resolver})
		
	def mkview(self,
		context=[],
		viewobj=None):
                """
        Make a new view in a given context
        arguments:
                context - a list giving the path to the required context
                viewobj - a View object
        returns:
                None on success
                a string error message on error
                """
		if viewobj == None:
			raise ValueError, "mkview: viewobj is None"
		return jsoncall.do_call(self.modelserver, self.modelport, "mkview", {'modelname':self.modelname,\
										'user':self.user,\
                                                                                'password':self.password,\
                                                                                'context':context,\
                                                                                'viewobj':viewobj.__dict__})
	def delview(self,
		context=[],
		viewid=None):
                """
        Delete an existing view in a given context
        arguments:
                context - a list giving the path to the required context
                viewid - the id for the view
        returns:
                None on success
                """
		if viewid == None:
			raise ValueError, "delview: viewid is None"
		return jsoncall.do_call(self.modelserver, self.modelport, "delview", {'modelname':self.modelname,\
										'user':self.user,\
                                                                                'password':self.password,\
                                                                                'context':context,\
                                                                                'viewid':viewid})

	
	def mkcontext(self, 
		context= [],
		contextobj=None):
		"""
	Make a new context in a given context
	arguments:
		context - a list giving the path to the required context 
		contextobj - a Context object
		"""
		if contextobj == None:
			raise ValueError, "mkcontext: contextobj is None"
		return jsoncall.do_call(self.modelserver, self.modelport, "mkcontext", {'modelname':self.modelname,\
										'user':self.user,\
                                                                                'password':self.password,\
                                                                                'context':context,\
                                                                                'contextobj':contextobj.__dict__})



	def subscribe(self,
		context=[],
		view=None,
		subscription=None):
		"""
	arguments:
		context is a list giving the path of context identifiers
		view is either:
			an identifier of a view in the context specified
			a list of component identifiers or full path lists
			None indicating that the values of all components in
				the context be returned
			subscription is a Subscription object
		"""
		return  jsoncall.do_call(self.modelserver, self.modelport, "subscribe", {'modelname':self.modelname,\
										'user':self.user,\
										'password':self.password,\
										'context':context,\
										'view':view,\
										'subscription':subscription})
	def delete_sub(self,
		context=[],
		componentid=None,
		subname=None):
		"""
	arguments:
		context is a list giving the path of context identifiers
		componentid designates the component subscribed to
		subname is the subscription name
		"""
		return  jsoncall.do_call(self.modelserver, self.modelport, "delete_sub", {'modelname':self.modelname,\
										'user':self.user,\
										'password':self.password,\
										'context':context,\
										'componentid':componentid,\
										'subname':subname})

	def export_model(self,
		context=[],
		evidence_filter=None):
		"""
	arguments:
		context is the context to export
		evidence_filter determines what evidence to export, None means none.
		"""
		return jsoncall.do_call(self.modelserver, self.modelport, "export_model", {'modelname':self.modelname,\
										'user':self.user,\
										'password':self.password,\
										'context':context,\
										'evidence_filter':evidence_filter})

	def import_model(self,
		context=[],
		partial_model=None):
		"""
	arguments:
		context is the context to import into
		partial_model is a json encoded string containing the partial model
		"""
		return jsoncall.do_call(self.modelserver, self.modelport, "import_model", {'modelname':self.modelname,\
										'user':self.user,\
										'password':self.password,\
										'context':context,\
										'partial_model':partial_model})
	def set_goals(self,
		context=[],
		componentid=None,
		goals=None):
		"""
	arguments:
		context is a list giving the path of context identifiers
		componentid designates the component with subscriptions attached
		goals is a list of paths to components that are:
			goals for this componentid if it is not of type goal
			components that contribute to this componentid if it is of type goal
		"""
		return  jsoncall.do_call(self.modelserver, self.modelport, "set_goals", {'modelname':self.modelname,\
										'user':self.user,\
										'password':self.password,\
										'context':context,\
										'componentid':componentid,\
										'goals':goals})

		
	def list_subs(self,
		context=[],
		componentid=None):
		"""
	arguments:
		context is a list giving the path of context identifiers
		componentid designates the component with subscriptions attached
		"""
		return  jsoncall.do_call(self.modelserver, self.modelport, "list_subs", {'modelname':self.modelname,\
										'user':self.user,\
										'password':self.password,\
										'context':context,\
										'componentid':componentid})

        def registerapp(self, app=None, desc="", password=None):
                """
                        registers a password for an app
                        app name is a string (needs checking TODO)
                        app passwords are stored at the top level .model db
                """
		return jsoncall.do_call(self.modelserver, self.modelport, "registerapp", {'modelname':self.modelname,\
                                                                                'user':self.user,\
										'password':self.password,\
										'app':app,\
										'description':desc,\
										'apppassword':password})
	
	def deleteapp(self, app=None):
                """
                        deletes an app
                """
 		if app == None:
			raise ValueError, "deleteapp: app is None"
		return jsoncall.do_call(self.modelserver, self.modelport, "deleteapp", {'modelname':self.modelname,\
                                                                                'user':self.user,\
                                                                                'password':self.password,\
                                                                                'app':app})

	def listapps(self):
		"""
			returns array of registered app names
		"""
		return jsoncall.do_call(self.modelserver, self.modelport, "listapps", {'modelname':self.modelname,\
										'user':self.user,\
										'password':self.password})

        def setpermission(self, context=None, componentid=None, app=None, permissions={}):
                """
                        sets ask/tell permission for a context (if componentid is None) or
                                a component
                """
 		return jsoncall.do_call(self.modelserver, self.modelport, "setpermission", {'modelname':self.modelname,\
										'user':self.user,\
										'password':self.password,\
										'context': context,\
										'componentid': componentid,\
										'app': app,\
										'permissions': permissions})

	def getpermission(self, context=None, componentid=None, app=None):
                """
                        gets permissions for a context (if componentid is None) or
                                a component
                        returns a tuple (ask,tell)
                """
		return jsoncall.do_call(self.modelserver, self.modelport, "getpermission", {'modelname':self.modelname,\
                                                                                'user':self.user,\
                                                                                'password':self.password,\
                                                                                'context': context,\
                                                                                'componentid': componentid,\
                                                                                'app': app})

class Personis_server:
	def __init__(self, modeldir=None):
		self.modeldir = modeldir

	def default(self, *args):
		try:
			jsonobj = cherrypy.request.body.read()
			pargs = json.loads(jsonobj)
		except:
                        print "bad request - cannot decode json - possible access from web browser"
                        return json.dumps("Personis User Model server. Not accessible using a web browser.")

		# dirty kludge to get around unicode
		for k,v in pargs.items():
			if type(v) == type(u''):
				pargs[k] = str(v)
			if type(k) == type(u''):
				del pargs[k]
				pargs[str(k)] = v

		try:			
			result = False
			if args[0] == 'mkmodel':
				# fixme need to implement security
				# and error handling
				Personis_base.MkModel(model=pargs['modelname'], modeldir=self.modeldir, \
							user=pargs['user'], password=pargs['password'], description=pargs['description'])
				result = True
			else:
				um = Personis_a.Access(model=pargs['modelname'], modeldir=self.modeldir, user=pargs['user'], password=pargs['password'])
	
			if args[0] == 'access':
				result = True
			elif args[0] == 'tell':
				result = um.tell(context=pargs['context'], componentid=pargs['componentid'], evidence=Personis_base.Evidence(**pargs['evidence']))
			elif args[0] == 'ask':
				reslist = um.ask(context=pargs['context'], view=pargs['view'], resolver=pargs['resolver'], \
							showcontexts=pargs['showcontexts'])
				if pargs['showcontexts']:
					cobjlist, contexts, theviews, thesubs = reslist
					cobjlist = [c.__dict__ for c in cobjlist]
					for c in cobjlist:
						if c["evidencelist"]:
							c["evidencelist"] = [e.__dict__ for e in c["evidencelist"]]
					newviews = {}
					if theviews != None:
						for vname,v in theviews.items():
							newviews[vname] = v.__dict__
					else:
						newviews = None
					reslist = [cobjlist, contexts, newviews, thesubs]
				else:
					reslist = [c.__dict__ for c in reslist]
					for c in reslist:
						if c["evidencelist"]:
							c["evidencelist"] = [e.__dict__ for e in c["evidencelist"]]
				result = reslist

			elif args[0] == 'subscribe':
				result = um.subscribe(context=pargs['context'], view=pargs['view'], subscription=pargs['subscription'])
			elif args[0] == 'delete_sub':
				result = um.delete_sub(context=pargs['context'], componentid=pargs['componentid'], subname=pargs['subname'])
			elif args[0] == 'list_subs':
				result = um.list_subs(context=pargs['context'], componentid=pargs['componentid'])
			elif args[0] == 'export_model':
				result = um.export_model(context=pargs['context'], evidence_filter=pargs['evidence_filter'])
			elif args[0] == 'import_model':
				result = um.import_model(context=pargs['context'], partial_model=pargs['partial_model'])
			elif args[0] == 'set_goals':
				result = um.set_goals(context=pargs['context'], componentid=pargs['componentid'], goals=pargs['goals'])
			elif args[0] == 'registerapp':
				result = um.registerapp(app=pargs['app'], desc=pargs['description'], password=pargs['apppassword'])
			elif args[0] == 'deleteapp':
				result = um.deleteapp(app=pargs['app'])
			elif args[0] == 'getpermission':
				result = um.getpermission(context=pargs['context'], componentid=pargs['componentid'], app=pargs['app'])
			elif args[0] == 'setpermission':
				result = um.setpermission(context=pargs['context'], componentid=pargs['componentid'], app=pargs['app'], permissions=pargs['permissions'])
			elif args[0] == 'listapps':
				result = um.listapps()
			elif args[0] == 'mkcomponent':
				comp = Personis_base.Component(**pargs["componentobj"])
				result = um.mkcomponent(pargs["context"], comp)
			elif args[0] == 'delcomponent':
				result = um.delcomponent(pargs["context"], pargs["componentid"])
			elif args[0] == 'delcontext':
				result = um.delcontext(pargs["context"])
			elif args[0] == 'setresolver':
				result = um.setresolver(pargs["context"], pargs["componentid"], pargs["resolver"])
			elif args[0] == 'getresolvers':
				result = um.getresolvers()
			elif args[0] == 'mkview':
				viewobj = Personis_base.View(**pargs["viewobj"])
				result = um.mkview(pargs["context"], viewobj)
			elif args[0] == 'delview':
				result = um.delview(pargs["context"], pargs["viewid"])
			elif args[0] == 'mkcontext':
				contextobj = Personis_base.Context(**pargs["contextobj"])
				result = um.mkcontext(pargs["context"], contextobj)

				
			# Repackage result code with error values IF there is a version string. 
			if pargs.has_key("version"):
				new_result = {}
				new_result["result"] = "ok"
				new_result["val"] = result
				result = new_result				
					
		except Exception, e:
			
			print e
			traceback.print_exc()
			if pargs.has_key("version"):
				new_result = {}
				#new_result["errorType"] = e.__class__.__name__
				#new_result["errorData"] = e.__dict__.copy()
				#new_result["pythonPickel"] = cPickle.dumps(e)
				new_result["val"] = [e.__class__.__name__, e.__dict__.copy(), cPickle.dumps(e)]
				new_result["result"] = "fail"
				result = new_result
			else:
				result = False
		
		return json.dumps(result)
		
	default.exposed = True

if __name__ == '__main__':
	if len(sys.argv) == 2:
		modeldir = sys.argv[1]
	else:
		modeldir = 'models'
	cherrypy.root = Personis_server(modeldir)
	conf = os.path.join(os.path.dirname(__file__), 'personis.conf')
	cherrypy.config.update(file = conf)
	cherrypy.server.start()

