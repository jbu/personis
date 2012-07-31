
Client/Server Protocol
======================

.. highlight:: python

This document describes the Personis *access*, *ask* and *tell* calls in terms of the Python method calls.

**access**::

	def access(modelname=string, user=string, password=string, version="11.2")

The POST URL is then /access and the body is (for example)::

	{"password": "pass", "modelname": "bob", "user": "bob", "version": "11.2"}

the return data is::

	{"result": "ok", "val": true}     -- on success
	{"result": "fail", "val": false}     -- on failure
	I might change this to include a diagnostic string as the value of val.


**tell**::

	def tell(modelname=string, user=string, password=string, version="11.2", 
                context=list-of-strings, componentid=string, evidence=dict)

The URL is /tell

Body example::

	{"modelname": "bob", 
	"user": "bob", 
	"password": "pass", 
	"version": "11.2", 
	"evidence": {"comment": null, "evidence_type": "explicit", "value": "Bob", 
	                "objectType": "Evidence", "source": "demoex2", "flags": [], 
	                "time": null, "exp_time": 0}, 
	"context": ["Personal"], 
	"componentid": "firstname"}

Note that the evidence dictionary should be extensible, ie not just the fields shown. Keys are strings, values can be strings/None/integer/list-of-strings

The return data is::

	{"result": "ok", "val": true}     -- on success
	{"result": "fail", "val": false}     -- on failure
	I might change this to include a diagnostic string as the value of val.[a]


**ask**::

	def ask(modelname=string, user=string, password=string, version="11.2", 
                context=list-of-strings, 
                resolve=dict,
                showcontexts=true-or-false,[b]
                view=list-of-(string-or-list-of-string) )

The resolver dictionary is extensible, keys and values are strings, *view* is a list of strings or (list of strings)

The URL is /ask

Body example::

	{"modelname": "bob", 
	"user": "bob", 
	"password": "pass", 
	"version": "11.2", 
	"context": ["Preferences", "Music", "Jazz", "Artists"], 
	"showcontexts": null,
	"resolver": {"evidence_filter": "all"}, 
	"view": ["Miles_Davis", ["Personal", "firstname"]]}

The return data is a dictionary containing a result and val entries like the Access function.
The value for "val" is a list of dictionaries, one per component value being returned.

example::

	{"result": "ok", "val": 
	 [        {"Description": "First name", 
	        "component_type": "attribute", 
	        "evidencelist": null, 
	        "value_list": null, 
	        "value": "Bob", 
	        "value_type": "string", 
	        "goals": [], 
	        "resolver": null, 
	        "Identifier": "firstname", 
	        "objectType": "Component"}, 
	        {"Description": "Last name", 
	        "component_type": "attribute", 
	        "evidencelist": null, 
	        "value_list": null, 
	        "value": "Kummerfeld", 
	        "value_type": "string", 
	        "goals": [], 
	        "resolver": null, 
	        "Identifier": "lastname", 
	        "objectType": "Component"}
	 ]
	}


The POST requests should be over HTTP for now, HTTPS later. Also, a future stage of development will involve more crypto with signed, encrypted JSON.

