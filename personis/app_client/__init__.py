import urllib2
import json

class Model(object):

	def __init__(self, server_uri, model, user, password):
		self.model = model
		self.uri = server_uri
		self.user = user
		self.password = password

	def _call(self, method, args):
		args["version"] = "11.2"
	    args_json = json.dumps(args)+'\n'

	    uri = self.uri + method
	    logging.info('call uri: %s, body: %s', uri, args_json)
	    req = urllib2.Request(url=uri, method="POST", headers={'Content-Type': 'application/json'}, data=args_json)
	    f = urllib2.urlopen()
	    return json.loads(f.read())

	def ask(self, context=[], view=None, resolver=None, showcontexts=None):

        reslist = _call("ask", {'modelname':self.model,\
                                'user':self.user,\
                                'password':self.password,\
                                'context':context,\
                                'view':view,\
                                'resolver':resolver,\
                                'showcontexts':showcontexts}
                        )

