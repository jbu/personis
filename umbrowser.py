#!/usr/bin/env python

import sys
import time
import Personis
import Personis_a
import Personis_base 
import Personis_mkmodel 
import simplejson as json
import json as sysjson

import cmd

class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

# utility function to display an object
def showobj(obj, indent):
	print "showobj:"
        for k,v in obj.__dict__.items():
		if ((k == 'time') or (k == 'creation_time')) and (v != None):
			print "%*s %s %s %s (%s)" % (indent, " ", k,"=",time.ctime(v),v)
		elif k == "evidencelist":
			print "%*s %s %s %d items" % (indent, " ", k,"=",len(v))
		else:
			print "%*s %s %s %s" % (indent, " ", k,"=",v)


# utility to print a list of component objects + evidence if printev="yes"
def printcomplist(reslist, printev=None, count=1):
	print "count =", count
	for res in reslist:
		print "==================================================================="
		print "Component: ", res.Description
		print "==================================================================="
		showobj(res, 0)
		if res.value_type == "JSON":
			jval = json.loads(res.value)
			print "Value:",jval
		if printev == "yes":
			print "---------------------------------"
			print "Evidence about it"
			print "---------------------------------"
			if res.evidencelist is None:
				print "no evidence"
			else:
				evlist = res.evidencelist
				evlist.reverse()
				for ev in evlist[:count]:
					if type(ev) == type(dict()):
						showobj(Struct(**ev), 10)
					else:
						showobj(ev, 10)
					print "---------------------------------"


def printjson(jsonobj):
	sysjson.dump(sysjson.loads(jsonobj), sys.stdout, sort_keys=True, indent=4)
	print

def loggedin(username, userpassword, cmd):
	if (username == None) or (userpassword == None):
		print cmd, ": please login"
		return False
	return True

def nomodel(modelname,cmd):
	if modelname == "":
		print cmd, ": please select a model using the 'model' command"
		return False
	return True

def lscontext(cont):
	global um
	try:
		info = um.ask(context=cont, showcontexts=True)
		(cobjlist, contexts, theviews, thesubs) = info
		#printcomplist(cobjlist, printev = "yes")
		print "Components:"
		for cobj in cobjlist:
			print "\t%s: %s"%(cobj.Identifier, cobj.Description)
		print "Contexts: %s" % str(contexts)
		print "Views: %s" % str(theviews)
		print "Subscriptions: %s" % str(thesubs)
	except ValueError, e:
		print "ask failed: %s" % (e)


um = None

class browse(cmd.Cmd):
	username = None
	userpassword = None
	accesstype = "base"
	attrs = {"voluble":False, "evnum":1}
	umname = ""
	context = [""]
	intro = "Personis Model Browser"
	prompt = "%s %s > " %(umname, context)
	def do_set(self, line):
		"""
		usage: set atrr-name value
		gives an attribute a value, eg 
			set evnum 5 
		will set the number of evidence items to print to 5
		"""
		global um, umname, context, username, attrs
		if not loggedin(self.username, self.userpassword, 'set'): return
		line = line.split()
		if len(line) != 2:
			print "usage: set atrr-name value"
			return
		if line[0] not in self.attrs:
			print "illegal attribute"
			return
		val = line[1]
		if line[1] == "True":
			val = True
		if line[1] == "False":
			val = False
		self.attrs[line[0]] = val
	
	def do_attributes(self, line):
		"""attributes lists current attributes 
			use the set command to set an attribute"""
		global um, umname, context, username, attrs
		if not loggedin(self.username, self.userpassword, 'attrs'): return
		print self.attrs
	
	def do_model(self, line):
		"""model modelname [modeldirectory]"""
		global um, umname, modeldir
		if not loggedin(self.username, self.userpassword, 'model'): return
		line = line.split()
		if len(line) == 0:
			if self.accesstype == "server":
				print "usage: model modelname"
				return
			else:
				print "usage: model modelname modeldirectory"
				return
		self.umname = line[0]
		if self.accesstype == "base":
			if len(line) != 2:
				print "usage: model modelname modeldirectory"
				return
			else:
				modeldir = line[1]
			try:
				um = Personis_a.Access(model=self.umname, modeldir=modeldir, user=self.username, password=self.userpassword)
			except:
				print "Failed to access model '%s', modeldir '%s', user '%s', password '%s'" % (self.umname, modeldir, self.username, self.userpassword)
				return
		else:
			try:
				um = Personis.Access(model=self.umname, user=self.username, password=self.userpassword)
			except:
				print "Failed to access model '%s', user '%s', password '%s'" % (self.umname, self.username, self.userpassword)
				return
			
		print "model '%s' open, access type is '%s'" % (self.umname, self.accesstype)
	
	def do_quit(self, line):
		"""quit the model browser"""
		print "Goodbye!"
		sys.exit(0)
	
	def do_ls(self, line):
		"""ls contextname|componentname"""
		global um, umname, context
		if not loggedin(self.username, self.userpassword, 'ls'): return
		if not nomodel(self.umname, line): return
		line = line.split()
		cont = self.context
		if len(line) == 1:
			if line[0][-1] == '/':
				lscontext(self.context+[line[0][:-1]])
			else:
				try:
					info = um.ask(context=self.context, view=[line[0]], resolver=dict(evidence_filter="all"))
					printcomplist(info, printev="yes", count=int(self.attrs["evnum"]))
				except ValueError, e:
					print "ask failed: %s" % (e)
		else:
			lscontext(self.context)
	
	def do_tell(self, line):
		"""tell component_name
			will prompt for component value etc"""
		global um, umname, context, username
		if not loggedin(self.username, self.userpassword, 'tell'): return
		if not nomodel(self.umname, line): return
		line = line.split()
		if len(line) != 1:
			print "usage: tell component"
			return
		compname = line[0]
		val = raw_input("Value? ")
		print "Evidence type:"
		for et in Personis_base.EvidenceTypes:
			print Personis_base.EvidenceTypes.index(et), et
		etindex = raw_input("Index? [0]")
		if etindex == '':
			etindex = 0
		else:
			etindex = int(etindex)
		if (etindex < 0) or (etindex > len(Personis_base.EvidenceTypes)-1):
			print "Index out of range"
			return
		etype = Personis_base.EvidenceTypes[etindex]
		source = self.username
		flags = []
		while True:
			flag = raw_input("Evidence flag? (CR for none)")
			if flag == '':
				break
			flags.append(flag)
	
		print "Tell value=%s, type=%s, flags=%s, source=%s, context=%s, component=%s " % (val, etype, flags, source, self.context, compname)
		ok = raw_input("Ok?[N] ")
		if ok != 'Y':
			return
		ev = Personis_base.Evidence(source=source, evidence_type=etype, flags=flags, value=val)
		try:
			um.tell(context=self.context, componentid=compname, evidence=ev)
		except ValueError, e:
			print "tell failed: %s" % (e)
		
	
	
	def do_cd(self, line):
		"""cd context_name
			changes to a subcontext or parent context using .. """
		global um, umname, context
		if not loggedin(self.username, self.userpassword, 'cd'): return
		if not nomodel(self.umname, line): return
		line = line.split()
		savecontext = list(self.context)
		if len(line) == 1:
			if line[0] == '..': 
				if len(self.context) > 1:
					self.context = self.context[:-1]
				else:
					self.context = ['']
			else:
				self.context.append(line[0])
		else:
			self.context = ['']
		try:
			info = um.ask(context=self.context)
		except:
			print "context not found:", self.context
			self.context = savecontext
		self.prompt = "%s %s > " %(self.umname, self.context)
	
	def do_login(self, line):
		"""login username password"""
		global username, userpassword
		line = line.split()
		if len(line) == 2:
			self.username = line[0]
			self.userpassword = line[1]
		else:
			print "usage: login user password"
		print "username:", self.username
		print "password:", self.userpassword
	
	def do_base(self, line):
		"""sets the access type to a model in the local machine file system"""
		global accesstype
		self.accesstype = "base"
	def do_server(self, line):
		"""sets the access type to a model in a remote server"""
		global accesstype
		self.accesstype = "server"
	
	def do_export(self, line):
		"""export filename
			exports current context to the given file in JSON form"""
		global um, context, attrs
		import json as sysjson
		if not loggedin(self.username, self.userpassword, 'export'): return
		if not nomodel(self.umname, line): return
		line = line.split()
		if len(line) != 1:
			print "usage: export tofilename"
			return
		try:
			expfile = open(line[0], "w")
		except:
			print "export: cannot open ", line[0]
			return
	
		modeljson = um.export_model(context=self.context, evidence_filter="all")
		mm = sysjson.loads(modeljson)
		expfile.write(sysjson.dumps(mm,sort_keys=True,indent=4))
		if self.attrs["voluble"]:
			print modeljson
	
	def do_import(self, line):
		"""import fromfilename
			imports a model from the given file in JSON format"""
		global um, context, attrs
		if not loggedin(self.username, self.userpassword, 'import'): return
		if not nomodel(self.umname, line): return
		line = line.split()
		if len(line) != 1:
			print "usage: import fromfilename"
			return
		try:
			importfile = open(line[0], "r")
		except:
			print "import: cannot open ", line[0]
			return
		um.import_model(context=self.context, partial_model=importfile.read())
		importfile.close()
	
	def do_importmdef(self, line):
		"""importmdef fromfilename
			imports a model in modeldef format"""
		global um, context, attrs
		if not loggedin(self.username, self.userpassword, 'importmdef'): return
		if not nomodel(self.umname, line): return
		line = line.split()
		if len(line) != 1:
			print "usage: importmdef fromfilename"
			return
		Personis_mkmodel.mkmodel_um(um,Personis_mkmodel.get_modeldef(line[0]))
		#try:
		#	Personis_mkmodel.mkmodel_um(um,Personis_mkmodel.get_modeldef(line[0]))
		#except:
		#	print "import modeldef failed"
	
	def do_setgoals(self, line):
		"""setgoals componentname goal-component [goal-component ...] """
		global um, context, attrs
		if not loggedin(self.username, self.userpassword, 'setgoals'): return
		if not nomodel(self.umname, line): return
		line = line.split()
		if len(line) < 2:
			print "usage: setgoals componentname goal-component [goal-component ...] "
			return
		comp = line[0]
		goals = [g.split('/') for g in line[1:]]
		um.set_goals(context=self.context, componentid=comp, goals=goals)
	
	def do_app(self, line):
		"""app application_name
			register a new app"""
		global um, context, attrs
		if not loggedin(self.username, self.userpassword, 'app'): return
		if not nomodel(self.umname, line): return
		line = line.split()
		if len(line) != 1:
			print "No new app specified"
			print "usage: app application_name"
			print "Registered applications:"
			print um.listapps()
			return
		appname = line[0]
		appdesc = raw_input("Application description: ")
		app_pass = raw_input("Application password: ")
		print um.registerapp(app=appname, desc=appdesc, password=app_pass)
	
	def do_setperm(self, line):
		"""setperm application_name
			set permissions for an application"""
		global um, context, attrs
		if not loggedin(self.username, self.userpassword, 'setperm'): return
		if not nomodel(self.umname, line): return
		line = line.split()
		if len(line) != 1:
			print "usage: setperm appname"
			return
		appname = line[0]
		apps = um.listapps()
		if not (appname in apps):
			print "app '%s' not registered"
			return
		contxt = self.context
		tellperm = raw_input("Tell ok? [N] ")
		if tellperm == '':
			tellperm = False
		elif tellperm == 'Y':
			tellperm = True
		elif tellperm == 'N':
			tellperm = False
		else:
			print "answer Y or N or enter for default"
		askperm = raw_input("Ask ok? [N] ")
		if askperm == '':
			askperm = False
		elif askperm == 'Y':
			askperm = True
		elif askperm == 'N':
			askperm = False
		else:
			print "answer Y or N or enter for default"
		print "Setting permission for app '%s': Ask=%s, Tell=%s  in context %s" % (appname, askperm, tellperm, contxt)
		ok = raw_input("Ok? [N] ")
		if ok != 'Y':
			print "Permissions NOT set"
			return
		um.setpermission(context=contxt, app=appname, permissions={'ask':askperm, 'tell':tellperm} )
		print "Permissions set"
	
	def do_showperm(self, line):
		"""showperm application_name
			displays permission information for an application"""
		global um, context, attrs
		if not loggedin(self.username, self.userpassword, 'showperm'): return
		if not nomodel(self.umname, line): return
		line = line.split()
		if len(line) != 1:
			print "usage: showperm appname"
			return
		appname = line[0]
		apps = um.listapps()
		if not (appname in apps):
			print "app '%s' not registered"
			return
		contxt = raw_input("Context path: ")
		contxt = contxt.split('/') 
		print "Permissions for app '%s' in context %s:" % (appname, contxt)
		print um.getpermission(context=contxt, app=appname)
	
	def do_subscribe(self, line):
		"""subscribe component_name
			add a subscription rule to a component"""
		global um, context, attrs
		if not loggedin(self.username, self.userpassword, 'subscribe'): return
		if not nomodel(self.umname, line): return
		line = line.split()
		if len(line) != 1:
			print "usage: subscribe component-name"
			return
		contxt = self.context
		comp = line[0]
		sub = raw_input("Subscription statement: ")
		print "Subscribing for component '%s' in context %s, with statement:\n%s" % (comp, contxt, sub)
		sub = {'user':self.username, 'password':self.userpassword, 'statement':sub}
		ok = raw_input("Ok? [N] ")
		if ok != 'Y':
			return
		um.subscribe(context=contxt, view=[comp], subscription=sub)
	
	def do_delsub(self, line):
		"""delsub component_name
			delete a subscription rule from a component"""
		global um, context, attrs
		if not loggedin(self.username, self.userpassword, 'delsub'): return
		if not nomodel(self.umname, line): return
		line = line.split()
		if len(line) != 1:
			print "usage: delsub compname"
			return
		contxt = self.context
		comp = line[0]
		print "Deleting subscriptions in context %s, component '%s'" % (contxt, comp)
		reslist = um.ask(context=contxt, view=[comp], showcontexts=True)
		cobjlist, contexts, theviews, thesubs = reslist
		thesubs = thesubs[comp]
		if thesubs == {}:
			print "Component '%s' has no subscriptions" % (comp)
			return
		for sid, sub in thesubs.items():
			d = raw_input("delete sub '%s'?[N] "%sub)
			if d == 'Y':
				result = um.delete_sub(context=contxt, componentid=comp, subname=sid)
				print result
	
	def do_mkcomponent(self, line):
		"""mkcomponent component_name
			make a new component"""
		global um, context, attrs
		if not loggedin(self.username, self.userpassword, 'mkcomponent'): return
		if not nomodel(self.umname, line): return
		line = line.split()
		if len(line) != 1:
			print "usage: mkcomponent compname"
			return
		contxt = self.context
		comp = line[0]
		compdesc = raw_input("Component description? ")
		print "Component type:"
		for ct in Personis_base.ComponentTypes:
			print Personis_base.ComponentTypes.index(ct), ct
		ctindex = int(raw_input("Index? "))
		if (ctindex < 0) or (ctindex > len(Personis_base.ComponentTypes)-1):
			print "Index out of range"
			return
		comptype = Personis_base.ComponentTypes[ctindex]
	
		print "Value type:"
		for ct in Personis_base.ValueTypes:
			print Personis_base.ValueTypes.index(ct), ct
		ctindex = int(raw_input("Index? "))
		if (ctindex < 0) or (ctindex > len(Personis_base.ValueTypes)-1):
			print "Index out of range"
			return
		valtype = Personis_base.ValueTypes[ctindex]
	
		print "Creating new component '%s', type '%s', description '%s', value type '%s'" % (comp, comptype, compdesc, valtype)
		ok = raw_input("Ok?[N] ")
		if ok != 'Y':
			return
		cobj = Personis_base.Component(Identifier=comp, component_type=comptype, Description=compdesc, value_type=valtype)
		res = um.mkcomponent(context=contxt,  componentobj=cobj)
	
	def do_delcomponent(self, line):
		"""delcomponent component_name
			delete a component"""
		global um, context, attrs
		if not loggedin(self.username, self.userpassword, 'delcomponent'): return
		if not nomodel(self.umname, line): return
		line = line.split()
		if len(line) != 1:
			print "usage: delcomponent compname"
			return
		comp = line[0]
		print "Deleting component '%s' in context %s" % (comp, self.context)
		ok = raw_input("Ok?[N] ")
		if ok != 'Y':
			return
		res = um.delcomponent(context=self.context, componentid=comp)
		if res:
			print res
	
	
	def do_mkcontext(self, line):
		"""mkcontext context_name
			make a new context"""
		global um, context, attrs
		if not loggedin(self.username, self.userpassword, 'mkcontext'): return
		if not nomodel(self.umname, line): return
		line = line.split()
		if len(line) != 1:
			print "usage: mkcontext contextname"
			return
		newcontext = line[0]
		contextdesc = raw_input("Context description? ")
		print "Create new context '%s' in context '%s' with description '%s'" % (newcontext, self.context, contextdesc)
		ok = raw_input("Ok?[N] ")
		if ok != 'Y':
			return
		cobj = Personis_base.Context(Identifier=newcontext, Description=contextdesc)
		if not um.mkcontext(self.context, cobj):
			print "Failed to make context. May be already present"
	
	def do_listapps(self, line):
		"""listapps
			list registered applications"""
		global um, context, attrs
		if not loggedin(self.username, self.userpassword, 'registerapp'): return
		if not nomodel(self.umname, line): return
		print um.listapps()
	
	def do_delapp(self, line):
		"""delapp appname
			delete an application
		"""
		global um, context, attrs
		if not loggedin(self.username, self.userpassword, 'delapp'): return
		if not nomodel(self.umname, line): return
		line = line.split()
		if len(line) > 1:
			print "usage: delapp [name]"
			return
		if len(line) == 1:
			um.deleteapp(line[0])
			return
		applist = um.listapps()
		for appname in applist:
			ok = raw_input("Delete app '%s'? [N] " % (appname))
			if ok == 'Y':
				um.deleteapp(appname)
	
	def do_mkmodel(self, line):
		"""mkmodel model_name [model_directory]
			makes a new empty model
			uses username, password specified in login cmd"""
		global umname, modeldir, username, userpassword
		if not loggedin(self.username, self.userpassword, 'mkmodel'): return
		line = line.split()
		if self.accesstype == "base":
			if len(line) != 2:
				print "usage: mkmodel model_name model_directory"
				return
			self.umname = line[0]
			modeldir = line[1]
			print "making model '%s' in directory '%s' with username '%s' and password '%s'" % (self.umname, modeldir, self.username, self.userpassword)
			try:
				Personis_base.MkModel(model=self.umname, modeldir=modeldir, user=self.username, password=self.userpassword)
			except Exception, e:
				print "mkmodel failed: ", e
				return
			print "model made"
			print "to access the model, use the command 'model %s %s'" % (self.umname, modeldir)
		else:
			print "can only make models locally at present"
		
	def do_do(self, line):
		"""do filename
			execute browser commands from a file, then switch back to interactive mode"""
		line = line.split()
		if len(line) != 1:
			print "usage: do cmdfile"
		else:
			with open(line[0]) as f:
				input = [x for x in f.read().splitlines() if x[0] != "#"]
			for line in input:
				print ">>%s" % (line)
			self.cmdqueue.extend(input)
		
	
browse().cmdloop()
