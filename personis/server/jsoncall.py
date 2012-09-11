
# The Personis system is copyright 2000-2012 University of Sydney
#       Bob.Kummerfeld@Sydney.edu.au

# This file is part of Personis.

# Personis is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Personis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Personis.  If not, see <http://www.gnu.org/licenses/>.

import httplib2, types, cPickle
import json
import cherrypy, oauth2client
#from ..client import Connection

def do_call(fun, args, connection):
	if (not connection.valid()):
		raise SystemError('Need http or modelserver and credentials')
	args["version"] = "11.2"
	args_json = json.dumps(args)+'\n'

	http = connection.get_http()

	resp, content = http.request(connection.uri+fun, "POST", body=args_json)

	try:
		result = json.loads(content)
	except:
		print "json loads failed!"
		print "<<%s>>" % (content)
		raise ValueError("json loads failed")
	# dirty kludge to get around unicode
	for k,v in result.items():
		if type(v) == type(''):
			result[k] = str(v)
		if type(k) == type(''):
			del result[k]
			result[str(k)] = v
	## Unpack the error, and if it is an exception throw it.
	if type(result) == dict and 'result' in result:
		if result["result"] == "error":
			print result
			# We have returned with an error, so throw it as an exception.
			if 'pythonPickel' in result:
				raise cPickle.loads(result["pythonPickel"])
			elif len(result["val"]) == 3:
				raise cPickle.loads(str(result["val"][2]))
			else:
				raise Exception(str(result["val"]))
		else:
			# Unwrap the result, and return as normal. 
			result = result["val"]
		return result
