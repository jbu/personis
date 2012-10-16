import urllib2
import json
import logging
from ..client import Component, Evidence

class Model(object):

	def __init__(self, server_uri, model, app, password):
		self.model = model
		self.uri = server_uri
		self.app = app
		self.password = password

	def _call(self, method, args):
		args["version"] = "11.2"
		args_json = json.dumps(args)+'\n'

		uri = self.uri + method
		logging.info('call uri: %s, body: %s', uri, args_json)
		req = urllib2.Request(url=uri, headers={'Content-Type': 'application/json'}, data=args_json)
		f = urllib2.urlopen(req)
		r = f.read()
		j = json.loads(r)
		return j['val']

	def ask(self, context=[], view=None, resolver=None, showcontexts=None):

		reslist = self._call("ask", {'modelname':self.model,\
			'user':self.app,\
			'password':self.password,\
			'context':context,\
			'view':view,\
			'resolver':resolver,\
			'showcontexts':showcontexts}
			)
		complist = []
		if showcontexts:
			cobjlist, contexts, theviews, thesubs = reslist
			for c in cobjlist:

				comp = Component(**c)
				if c["evidencelist"]:
					comp.evidencelist = [Evidence(**e) for e in c["evidencelist"]]
				complist.append(comp)
			reslist = [complist, contexts, theviews, thesubs]
		else:
			for c in reslist:
				comp = Component(**c)
				if c["evidencelist"]:
					comp.evidencelist = [Evidence(**e) for e in c["evidencelist"]]
				complist.append(comp)
			reslist = complist
		return reslist
