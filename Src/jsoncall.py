
import httplib2, types, cPickle
import simplejson as json
import cherrypy, oauth2client

def do_call(credentials, fun, args):
	args["version"] = "11.2"
	args_json = json.dumps(args)+'\n'
	con = httplib2.Http()
	credentials.authorize(con)

	resp, content = con.request('http://localhost:2005/'+fun, "POST", body=args_json)
	try:
		result = json.loads(content)
	except:
		print "json loads failed!"
		print "<<%s>>" % (content)
		raise ValueError, "json loads failed"
	# dirty kludge to get around unicode
	for k,v in result.items():
		if type(v) == type(u''):
			result[k] = str(v)
		if type(k) == type(u''):
			del result[k]
			result[str(k)] = v
	## Unpack the error, and if it is an exception throw it.
	if type(result) == types.DictionaryType and result.has_key("result"):
		if result["result"] == "error":
			print result
			# We have returned with an error, so throw it as an exception.
			if result.has_key("pythonPickel"):
				raise cPickle.loads(result["pythonPickel"])
			elif len(result["val"]) == 3:
				raise cPickle.loads(str(result["val"][2]))
			else:
				raise Exception, str(result["val"])
		else:
			# Unwrap the result, and return as normal. 
			result = result["val"]
		return result
