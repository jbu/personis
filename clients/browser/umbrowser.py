#!/usr/bin/env python

import time
from personis import client
import json
from optparse import OptionParser
import yaml

from oauth2client.file import Storage
from oauth2client.client import Credentials, OAuth2WebServerFlow, flow_from_clientsecrets
from oauth2client.tools import run
import httplib2

import cmd


def printjson(jsonobj):
    json.dump(sysjson.loads(jsonobj), sys.stdout, sort_keys=True, indent=4)
    print

def loggedin(modelserver, credentials, cmd):
    if (credentials == None):
        print cmd, ": please login"
        return False
    return True

def nomodel(modelname,cmd):
    if modelname == "":
        print cmd, ": please select a model using the 'model' command"
        return False
    return True

def lscontext(um, cont):
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

    def __init__(self):
        self.accesstype = "base"
        self.attrs = {"voluble":False, "evnum":1}
        self.um = None
        self.username = ''
        self.context = [""]
        self.intro = "Personis Model Browser"
        self.prompt = "%s > " %(self.context)
        cmd.Cmd.__init__(self)

    def do_set(self, line):
        """
        usage: set atrr-name value
        gives an attribute a value, eg
                set evnum 5
        will set the number of evidence items to print to 5
        """
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
        print self.attrs

    def do_model(self, line):
        """model modelname [modeldirectory]"""
        return

        line = line.split()
        if len(line) == 0:
            print "usage: model modelname"
            return
        self.umname = line[0]
        try:
            self.um = client.Access(modelserver=self.modelserver, credentials=self.credentials)
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
        line = line.split()
        cont = self.context
        if len(line) == 1:
            if line[0][-1] == '/':
                lscontext(self.um, self.context+[line[0][:-1]])
            else:
                try:
                    info = self.um.ask(context=self.context, view=[line[0]], resolver=dict(evidence_filter="all"))
                    client.util.PrintComplist(info, printev="yes", count=int(self.attrs["evnum"]))
                except ValueError, e:
                    print "ask failed: %s" % (e)
        else:
            lscontext(self.um, self.context)

    def do_tell(self, line):
        """tell component_name
                will prompt for component value etc"""
        line = line.split()
        if len(line) != 1:
            print "usage: tell component"
            return
        compname = line[0]
        val = raw_input("Value? ")
        print "Evidence type:"
        for et in client.EvidenceTypes:
            print client.EvidenceTypes.index(et), et
        etindex = raw_input("Index? [0]")
        if etindex == '':
            etindex = 0
        else:
            etindex = int(etindex)
        if (etindex < 0) or (etindex > len(client.EvidenceTypes)-1):
            print "Index out of range"
            return
        etype = client.EvidenceTypes[etindex]
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
        ev = client.Evidence(source=source, evidence_type=etype, flags=flags, value=val)
        try:
            self.um.tell(context=self.context, componentid=compname, evidence=ev)
        except ValueError, e:
            print "tell failed: %s" % (e)



    def do_cd(self, line):
        """cd context_name
                changes to a subcontext or parent context using .. """

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
            info = self.um.ask(context=self.context)
        except:
            print "context not found:", self.context
            self.context = savecontext
        self.prompt = "%s > " %(self.context)

    def do_login(self, line):
        """login username password"""
        return

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
        self.accesstype = "base"

    def do_server(self, line):
        """sets the access type to a model in a remote server"""
        self.accesstype = "server"

    def do_export(self, line):
        """export filename
                exports current context to the given file in JSON form"""
        line = line.split()
        if len(line) != 1:
            print "usage: export tofilename"
            return
        try:
            expfile = open(line[0], "w")
        except:
            print "export: cannot open ", line[0]
            return

        modeljson = self.um.export_model(context=self.context, evidence_filter="all")
        mm = json.loads(modeljson)
        expfile.write(sysjson.dumps(mm,sort_keys=True,indent=4))
        if self.attrs["voluble"]:
            print modeljson

    def do_import(self, line):
        """import fromfilename
                imports a model from the given file in JSON format"""
        line = line.split()
        if len(line) != 1:
            print "usage: import fromfilename"
            return
        try:
            importfile = open(line[0], "r")
        except:
            print "import: cannot open ", line[0]
            return
        self.um.import_model(context=self.context, partial_model=importfile.read())
        importfile.close()

    #def do_importmdef(self, line):
    #    """importmdef fromfilename
    #            imports a model in modeldef format"""
    #    line = line.split()
    #    if len(line) != 1:
    #        print "usage: importmdef fromfilename"
    #        return
    #    Personis_mkmodel.mkmodel_um(um,Personis_mkmodel.get_modeldef(line[0]))
        #try:
        #       Personis_mkmodel.mkmodel_um(um,Personis_mkmodel.get_modeldef(line[0]))
        #except:
        #       print "import modeldef failed"

    def do_setgoals(self, line):
        """setgoals componentname goal-component [goal-component ...] """
        line = line.split()
        if len(line) < 2:
            print "usage: setgoals componentname goal-component [goal-component ...] "
            return
        comp = line[0]
        goals = [g.split('/') for g in line[1:]]
        self.um.set_goals(context=self.context, componentid=comp, goals=goals)

    def do_app(self, line):
        """app application_name
                register a new app"""
        line = line.split()
        if len(line) != 1:
            print "No new app specified"
            print "usage: app application_name"
            print "Registered applications:"
            print self.um.listapps()
            return
        appname = line[0]
        appdesc = raw_input("Application description: ")
        app_pass = raw_input("Application password: ")
        print self.um.registerapp(app=appname, desc=appdesc, password=app_pass)

    def do_setperm(self, line):
        """setperm application_name
                set permissions for an application"""
        line = line.split()
        if len(line) != 1:
            print "usage: setperm appname"
            return
        appname = line[0]
        apps = self.um.listapps()
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
        self.um.setpermission(context=contxt, app=appname, permissions={'ask':askperm, 'tell':tellperm} )
        print "Permissions set"

    def do_showperm(self, line):
        """showperm application_name
                displays permission information for an application"""
        line = line.split()
        if len(line) != 1:
            print "usage: showperm appname"
            return
        appname = line[0]
        apps = self.um.listapps()
        if not (appname in apps):
            print "app '%s' not registered"
            return
        contxt = raw_input("Context path: ")
        contxt = contxt.split('/')
        print "Permissions for app '%s' in context %s:" % (appname, contxt)
        print self.um.getpermission(context=contxt, app=appname)

    def do_subscribe(self, line):
        """subscribe component_name
                add a subscription rule to a component"""
        line = line.split()
        if len(line) != 1:
            print "usage: subscribe component-name"
            return
        contxt = self.context
        comp = line[0]
        sub = raw_input("Subscription statement: ")
        print "Subscribing for component '%s' in context %s, with statement:\n%s" % (comp, contxt, sub)
        sub = {'user':self.username, 'password':'', 'statement':sub}
        ok = raw_input("Ok? [N] ")
        if ok != 'Y':
            return
        self.um.subscribe(context=contxt, view=[comp], subscription=sub)

    def do_delsub(self, line):
        """delsub component_name
                delete a subscription rule from a component"""

        line = line.split()
        if len(line) != 1:
            print "usage: delsub compname"
            return
        contxt = self.context
        comp = line[0]
        print "Deleting subscriptions in context %s, component '%s'" % (contxt, comp)
        reslist = self.um.ask(context=contxt, view=[comp], showcontexts=True)
        cobjlist, contexts, theviews, thesubs = reslist
        thesubs = thesubs[comp]
        if thesubs == {}:
            print "Component '%s' has no subscriptions" % (comp)
            return
        for sid, sub in thesubs.items():
            d = raw_input("delete sub '%s'?[N] "%sub)
            if d == 'Y':
                result = self.um.delete_sub(context=contxt, componentid=comp, subname=sid)
                print result

    def do_mkcomponent(self, line):
        """mkcomponent component_name
                make a new component"""

        line = line.split()
        if len(line) != 1:
            print "usage: mkcomponent compname"
            return
        contxt = self.context
        comp = line[0]
        compdesc = raw_input("Component description? ")
        print "Component type:"
        for ct in client.ComponentTypes:
            print client.ComponentTypes.index(ct), ct
        ctindex = int(raw_input("Index? "))
        if (ctindex < 0) or (ctindex > len(client.ComponentTypes)-1):
            print "Index out of range"
            return
        comptype = client.ComponentTypes[ctindex]

        print "Value type:"
        for ct in client.ValueTypes:
            print client.ValueTypes.index(ct), ct
        ctindex = int(raw_input("Index? "))
        if (ctindex < 0) or (ctindex > len(client.ValueTypes)-1):
            print "Index out of range"
            return
        valtype = client.ValueTypes[ctindex]

        print "Creating new component '%s', type '%s', description '%s', value type '%s'" % (comp, comptype, compdesc, valtype)
        ok = raw_input("Ok?[N] ")
        if ok != 'Y':
            return
        cobj = client.Component(Identifier=comp, component_type=comptype, Description=compdesc, value_type=valtype)
        res = self.um.mkcomponent(context=contxt,  componentobj=cobj)

    def do_delcomponent(self, line):
        """delcomponent component_name
                delete a component"""
        line = line.split()
        if len(line) != 1:
            print "usage: delcomponent compname"
            return
        comp = line[0]
        print "Deleting component '%s' in context %s" % (comp, self.context)
        ok = raw_input("Ok?[N] ")
        if ok != 'Y':
            return
        res = self.um.delcomponent(context=self.context, componentid=comp)
        if res:
            print res


    def do_mkcontext(self, line):
        """mkcontext context_name
                make a new context"""

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
        if not self.um.mkcontext(self.context, cobj):
            print "Failed to make context. May be already present"

    def do_listapps(self, line):
        """listapps
                list registered applications"""

        print self.um.listapps()

    def do_delapp(self, line):
        """delapp appname
                delete an application
        """

        line = line.split()
        if len(line) > 1:
            print "usage: delapp [name]"
            return
        if len(line) == 1:
            self.um.deleteapp(line[0])
            return
        applist = self.um.listapps()
        for appname in applist:
            ok = raw_input("Delete app '%s'? [N] " % (appname))
            if ok == 'Y':
                self.um.deleteapp(appname)

    def do_mkmodel(self, line):
        """mkmodel model_name [model_directory]
                makes a new empty model
                uses username, password specified in login cmd"""
        return
        line = line.split()
        if self.accesstype == "base":
            if len(line) != 2:
                print "usage: mkmodel model_name model_directory"
                return
            umname = line[0]
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



if __name__ == '__main__':

    parser = OptionParser()
 
    parser.add_option("-o", "--oauthconf",
              dest="oauthconf", metavar='FILE',
              help="Oauth Config file", default='oauth.yaml')
    (options, args) = parser.parse_args()
    f = file(options.oauthconf,'r')
    httplib2.debuglevel = 0
    oauthconf = yaml.load(f)
    FLOW = flow_from_clientsecrets('client_secrets.json',
        scope='https://www.personis.com/auth/model')

    # If the Credentials don't exist or are invalid run through the native client
    # flow. The Storage object will ensure that if successful the good
    # Credentials will get written back to a file.
    storage = Storage('credentials.dat')
    credentials = storage.get()
    p = httplib2.ProxyInfo(proxy_type=httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL, proxy_host='www-cache.it.usyd.edu.au', proxy_port=8000)
    h = httplib2.Http(proxy_info=p)
    if credentials is None or credentials.invalid:
        credentials = run(FLOW, storage, h)
    cjson = json.loads(credentials.to_json())
    # Create an httplib2.Http object to handle our HTTP requests and authorize it
    # with our good Credentials.
    http = httplib2.Http(proxy_info=p)
    #http = credentials.authorize(http)
    b = browse()
    b.um = client.Access(uri = 'http://ec2-54-251-12-234.ap-southeast-1.compute.amazonaws.com:2005/', 
            credentials = credentials, http = http, debug=True)
    reslist = b.um.ask(context=["Personal"],view=['firstname'])
    client.util.PrintComplist(reslist)
    b.username = reslist[0].value
    print b.username

    b.cmdloop()
    #resp, content = http.request('https://www.googleapis.com/oauth2/v1/userinfo?access_token='+cjson['access_token'])
    #usr = json.loads(content)
    #global username
    #username = usr['email']
    #print username
