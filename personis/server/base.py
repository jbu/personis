#!/usr/bin/env python

#
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


"""
model database stored in ".model" in the model directory::

    Identifier  modelname
    Description     of the model
    owner       owner of the model
    password    md5 hash of owner password for this model
    apps        dictionary of app names and keys
        appname     dictionary of info about that app
            password    md5 hash of the apps access key (password)
            description of the app

context database stored in ".context" in each context directory::

    Identifier  context name
    Description     of the context
    perms       a dictionary of permissions for apps
        appname     dictionary of permission info for that app
            permname    True/False value indicates permname permission for the app
                eg {"ask":False, "tell":True} can tell values but not ask
            "resolvers" list of resolvers that the app is allowed to use
                eg {"resolvers":["last1", "goal"]}
"""

import os, shelve, sys, time, string, glob
import hashlib
from . import filedict
from types import *
from . import resolvers
from . import ev_filters
import json
from . import util
import logging
import traceback
from ..client import Evidence
from ..client import Context
from ..client import View
from ..client import Component as clientComponent
from ..client import Access as clientAccess

PERSONIS_VERSION = "$LastChangedRevision: 727 $"



def MkModel(model=None, modeldir=None, user=None, description=None):
    """make a model with name "model" in directory modeldir for "user" with "description"

    :param model:
    :param modeldir:
    :param user:
    :param description:
    :raise:
    """

    if modeldir == None:
        raise ValueError("modeldir is None in MkModel")
    modeldir = os.path.join(modeldir, model)
    os.mkdir(modeldir)
    mod, mod_shelf_fd = shelf_open(os.path.join(modeldir,".model"), "c")
    mod['Identifier'] = model
    mod['owner'] = user
    #p = hashlib.md5()
    #if password == None:
    #   password = ''
    #p.update(password)
    mod['password'] = '' #p.hexdigest()
    mod['apps'] = {} # dictionary of app names and keys
    mod['Description'] = description
    shelf_close(mod, mod_shelf_fd)
    con, con_shelf_fd = shelf_open(os.path.join(modeldir,".context"), "c")
    con['Identifier'] = '.'
    con['Description'] = 'root context'
    con['perms'] = {}
    shelf_close(con, con_shelf_fd)
    comps, comps_shelf_fd = shelf_open(os.path.join(modeldir,".components"), "c")
    shelf_close(comps, comps_shelf_fd)
    evdb,evdb_fd = shelf_open(os.path.join(modeldir,".evidence"), "c")
    shelf_close(evdb, evdb_fd)
    views, views_shelf_fd = shelf_open(os.path.join(modeldir,".views"), "c")
    shelf_close(views, views_shelf_fd)
    subs, subs_shelf_fd = shelf_open(os.path.join(modeldir,".subscriptions"), "c")
    shelf_close(subs, subs_shelf_fd)

def shelf_open(shelf_name, mode):
    db = filedict.FileDict(filename=shelf_name)
    return db, None
 
def shelf_close(theShelf, shelf_fd):
    pass
    #theShelf.close()

class Component(clientComponent):

    def filterevidence(self, model=None, context=[], resolver_args=None):
        """

        :param model:
        :param context:
        :param resolver_args:

        :return:
            if evidence_filter is "all": 
                returns all evidence objects for this component in a list
            if evidence_filter is "last10":
                return only the last 10 elements
            if evidence_filter is "last1":
                return only the last element
            if evidence_filter is None:
                return empty list
            else returns a list of evidence objects for which evidence_filter(evidence)
                return true

        """
        strId = self.Identifier
        if resolver_args == None:
            raise ValueError('no evidence filter')
        evidence_filter = resolver_args.get('evidence_filter')
        if evidence_filter == None:
            evidence_filter = 'all'
        if evidence_filter in model.evidencefilterlist:
            efilter = model.evidencefilterlist[evidence_filter]
        else:
            raise ValueError('unknown evidence filter "%s"'%(repr(evidence_filter)))

        try:
            evdb,evdb_fd = shelf_open(model._getcontextdir(context)+"/.evidence", "r")
        except:
            raise ValueError("tell: no evidence db for %s"%(repr(context)))
        
        evidence_list = []
        for k in evdb:
            if k.startswith(strId+':'):
                evidence_list += [evdb[k].__dict__]
        evidence_list = efilter(elist=evidence_list, arguments=resolver_args)

        shelf_close(evdb, evdb_fd)
        return evidence_list

    def getevidence(self, model=None, context=[], count=None):
        """if count is None, returns (last evidence obj, count)
            else returns (count evidence obj, count)
        """
        strId = self.Identifier
        try:
            evdb,evdb_fd = shelf_open(model._getcontextdir(context)+"/.evidence", "r")
        except:
            raise ValueError("tell: no evidence db for %s"%(repr(context)))
        if strId not in evdb:
            shelf_close(evdb, evdb_fd)
            return (None, None) # no evidence for this component
        if count == None:
            count = evdb[strId]
        if "%s:%d"%(strId,count) in evdb:
            evidence = evdb["%s:%d"%(strId,count)]
        else:
            evidence = None
        shelf_close(evdb, evdb_fd)
        return (evidence, count)

    def findevidence(self, model=None, context=[], evidence_time=None):
        """

        :param model:
        :param context:
        :param evidence_time:
        :return:
        :raise:
        """
        if evidence_time == None:
            raise ValueError("findevidence: no evidence time specified")
        try:
            evdb,evdb_fd = shelf_open(model._getcontextdir(context)+"/.evidence", "r")
        except:
            raise ValueError("tell: no evidence db for %s"%(repr(context)))
        if self.Identifier not in evdb:
            shelf_close(evdb, evdb_fd)
            return (None, None) # no evidence for this component
        count = evdb[self.Identifier]
        evidence = None
        while count > 0:
            if "%s:%d"%(self.Identifier,count) in evdb:
                evidence = evdb["%s:%d"%(self.Identifier,count)]
                break
            else:
                count = count-1
        if evidence == None:
            # no evidence found
            shelf_close(evdb, evdb_fd)
            return (None, None)

        lo = 0; hi = count
        while lo < hi:
            mid = (lo+hi)//2
            while mid > 0:
                if "%s:%d"%(self.Identifier,mid) in evdb:
                    evidence = evdb["%s:%d"%(self.Identifier,mid)]
                    break
                else:
                    mid = mid-1
            if mid == 0: # no more evidence found!
                shelf_close(evdb, evdb_fd)
                return (None, None)
                
            if evidence_time < evidence.time:
                hi = mid
            else:
                lo = mid+1
        # index of required evidence item is "lo"
        shelf_close(evdb, evdb_fd)
        return evidence,count


class Access(resolvers.Access, ev_filters.Access):
    """
    :param model: model name
    :param modeldir: model directory
    :param user: user name
    :param debug: password string
    :return: a user model access object 
    :raise:
    """

    def __init__(self, model=None, modeldir="", user='', password=None, debug=0):
        if model == None:
            raise ValueError("model is None")
        if modeldir[0] != '/':
            self.modeldir = os.getcwd()+'/'+modeldir
        else:
            self.modeldir = modeldir
        self.modelname = model
        self.user = user
        self.password = password
        self.debug = debug
        if not os.path.isdir(os.path.join(self.modeldir,self.modelname)):
            raise ValueError("no model dir for '%s'"%(self.modelname))
        try:
            mod,mod_shelf_fd = shelf_open(os.path.join(self.modeldir,self.modelname,".model"), "r")
        except:
            raise ValueError("no model db for '%s'"%(self.modelname))
        self.moddb = {}
        for k in mod:
            self.moddb[k] = mod[k]
        if (self.user == self.moddb['owner']) and self.password is None:
            self.usertype = 'owner'
        else:
            self.usertype = 'app'
            if self.user not in self.moddb['apps']:
                raise ValueError("App %s not registered in %s" % (self.user, model))

        shelf_close(mod, mod_shelf_fd)
        resolvers.Access.__init__(self)
        ev_filters.Access.__init__(self)

    def ask(self,  
        context=[],
        view=None,
        resolver=None,
        showcontexts=None):
        """

        :param context: a list giving the path of context identifiers
        :param view: either:
            - an identifier of a view in the context specified
            - a list of component identifiers or full path lists
            - None indicating that the values of all components in the context be returned
        :param resolver: 
            - a string containing the name of a resolver or
            - resolver is a dictionary containing information about resolver(s) to be used and arguments
                - the "resolver" key gives the name of a resolver to use, if not present the default resolver is used
                - the "evidence_filter" key specifies an evidence filter
                - eg 'evidence_filter' =  "all" returns all evidence,
                    - "last10" returns last 10 evidence items,
                    - "last1" returns most recent evidence item,
                    - None returns no evidence
        :param showcontexts: if True, a tuple is returned containing 
            (list of component objects, 
            list of contexts in the current context,
            list of views in the current context,
            list of subscriptions in the current context)
        :return: a list of component objects
        :raise:
        """
        logging.debug('ask: %s, %s, %s', context, view, resolver)
        self.curcontext = self._getcontextdir(context)
        contextinfo = self.getcontext(context)
        if 'perms' not in contextinfo:
            perms = []
            print 'no perms!'
        else:
            perms = contextinfo['perms']
        if self.usertype != 'owner':
            if self.user not in perms:
                raise ValueError("No permission for: %s in %s/%s" % (self.user, context, view))
        if self.usertype == 'app':
            if not self.checkpermission(context=context, componentid=None, app=self.user, permname='ask', permval=True):
                raise ValueError("No permission for: %s in %s/%s" % (self.user, context, view))
            
        try:
            comps,comps_shelf_fd = shelf_open(self.curcontext+"/.components", "r")
        except:
            comps = None
        try:
            views,views_shelf_fd = shelf_open(self.curcontext+"/.views", "r")
        except:
            views = None
        try:
            subs,subs_shelf_fd = shelf_open(self.curcontext+"/.subscriptions", "r")
        except:
            subs = None
        try:
            contexts = os.listdir(self.curcontext)
            contexts = [x for x in contexts if os.path.isdir(os.path.join(self.curcontext,x))]
        except OSError as e:
            raise ValueError("Component/Context not found: %s/%s" % (context, view))
        cidlist = []
        cobjlist = []

        if isinstance(view, basestring):
            if views != None:
                if view not in views:
                    raise ValueError('"%s" view not found'%(view))
                cidlist = views[view].component_list
            else:
                raise ValueError('"%s" view not found'%(view))
        elif type(view) is ListType:
            cidlist = view
        elif view == None: 
            if comps != None:
                cidlist = comps
        else:
            raise TypeError('view "%s" has unknown type'%(repr(view)))
        self.theresolver = None
        resolver_args = {}
        if resolver != None: 
            if type(resolver) == type({}):
                resolver_args = resolver.copy()
                resolver = resolver_args.get('resolver') # extract the string name of the resolver function
            if resolver != None:
                if resolver in self.resolverlist:
                    self.theresolver = self.resolverlist[resolver]
                else:
                    raise ValueError('unknown resolver "%s"'%(repr(resolver)))
        for cid in cidlist:
            if isinstance(cid, basestring):
                if comps != None:
                    if cid in comps:
                        if 'resolver' in comps[cid].__dict__:
                            compresname = comps[cid].resolver
                        else:
                            compresname = None
                        if 'resolver' in contextinfo:
                            contresname = contextinfo['resolver']
                        else:
                            contresname = None
                        if self.theresolver != None:
                            compresolver = self.theresolver
                        elif compresname == None:
                            if contresname != None:
                                if contresname in self.resolverlist:
                                    compresolver = self.resolverlist[contresname]
                                else:
                                    raise ValueError('unknown resolver "%s"'%(contresname))
                            else:
                                compresolver = self.resolverlist["default"]
                        elif compresname in self.resolverlist:
                            compresolver = self.resolverlist[compresname]
                        else:
                            raise ValueError('unknown resolver "%s"'%(compresname))
                        cobjlist.append(compresolver(model=self, 
                                                component=comps[cid],
                                                context=context, 
                                                resolver_args=resolver_args)
                                        )
                    else:
                        raise ValueError('component "%s" not in view "%s" (%s)'%(cid,view,cidlist))
                else:
                    raise ValueError('component "%s" not found'%(cid))
            elif type(cid) is ListType:
                vcontext = self._getcontextdir(cid[:-1])
                last_cid = cid[-1]
                try:
                    vcomps,vcomps_shelf_fd = shelf_open(vcontext+"/.components", "r")
                except:
                    raise ValueError('context "%s" not in view "%s"'%(last_cid,repr(view)))
                if last_cid in vcomps:
                    if 'resolver' in vcomps[last_cid].__dict__ :
                        compresname = vcomps[last_cid].resolver
                    else:
                        compresname = None
                    if self.theresolver != None:
                        compresolver = self.theresolver
                    elif compresname == None:
                        compresolver = self.resolverlist["default"]
                    elif compresname in self.resolverlist:
                        compresolver = self.resolverlist[compresname]
                    else:
                        raise ValueError('unknown resolver "%s"'%(compresname))
                    cobjlist.append(compresolver(model=self, component=vcomps[last_cid], \
                                context=context, resolver_args=resolver_args))
                else:
                    raise ValueError('component "%s" not in view "%s"'%(last_cid,repr(view)))
                shelf_close(vcomps, vcomps_shelf_fd)
                    
        if comps != None:
            shelf_close(comps, comps_shelf_fd)
        if views != None:
            theviews = {}
            for v in views:
                theviews[v] = views[v]
            shelf_close(views, views_shelf_fd)
        else:
            theviews = None
        if subs != None:
            thesubs = {}
            for s in subs:
                thesubs[s] = subs[s]
            shelf_close(subs, subs_shelf_fd)
        else:
            thesubs = None
        if showcontexts:
            return (cobjlist, contexts, theviews, thesubs)
        return cobjlist

    def export_model(self,
        context=[],
        resolver=None,
        level=None):
        """Export a model to a json representation

        :param context: a list giving the path of context identifiers this is the root of the um tree to export
        :param resolver: 
            - a string containing the name of a resolver or
            - a dictionary containing information about resolver(s) to be used and arguments
            - the "resolver" key gives the name of a resolver to use, if not present the default resolver is used
            - the "evidence_filter" key specifies an evidence filter
            - eg 'evidence_filter' =   "all" returns all evidence,
                - "last10" returns last 10 evidence items,
                - "last1" returns most recent evidence item,
                - None returns no evidence
        :param level:

        :return: returns a JSON encoded representation of the um tree
        :raise:
        """
        self.curcontext = self._getcontextdir(context)
        contextinfo = self.getcontext(context)
        perms = contextinfo['perms']
        if self.usertype != 'owner':
            if self.user not in perms:
                raise ValueError("No permission for: %s in %s/%s" % (self.user, context, view))
        if self.usertype == 'app':
            if not self.checkpermission(context=context, componentid=None, app=self.user, permname='ask', permval=True):
                raise ValueError("No permission for: %s in %s/%s" % (self.user, context, view))

        self.theresolver = None
        resolver_args = {}
        if resolver != None: 
            if type(resolver) == type({}):
                resolver_args = resolver.copy()
                resolver = resolver_args.get('resolver') # extract the string name of the resolver function
            if resolver != None:
                if resolver in self.resolverlist:
                    self.theresolver = self.resolverlist[resolver]
                else:
                    raise ValueError('unknown resolver "%s"'%(repr(resolver)))

        try:
            comps,comps_shelf_fd = shelf_open(self.curcontext+"/.components", "r")
        except:
            comps = None
        try:
            views,views_shelf_fd = shelf_open(self.curcontext+"/.views", "r")
        except:
            views = None
        try:
            subs,subs_shelf_fd = shelf_open(self.curcontext+"/.subscriptions", "r")
        except:
            subs = None
        try:
            contexts = os.listdir(self.curcontext)
            contexts = [x for x in contexts if os.path.isdir(self.curcontext+"/"+x)]
        except OSError as e:
            raise ValueError("Context not found: %s" % (context))
        
        if contexts != []:
            thecontexts = {}
            for con in contexts:
                thecontexts[con] = self.export_model(context=context+[con], resolver=resolver_args, level= level if level != None else 1)
        else:
            thecontexts = None

        if self.theresolver != None:
            compresolver = self.theresolver
        else:
            compresolver = self.resolverlist["default"]
        if comps != None:
            thecomps = {}
            for c in comps:
                #evlist = comps[c].filterevidence(model=self, context=context, resolver=resolver)
                #evlist2 = []
                #if type(evlist) == type([]):
                #   for e in evlist:
                #       evlist2.append(e.__dict__)
                #comps[c].__dict__["evidencelist"] = evlist2
                #thecomps[c] = comps[c].__dict__
                #thecomps[c]["evidencelist"] = evlist2
                thecomps[c] = compresolver(model=self, context=context, component=comps[c], resolver_args=resolver_args).__dict__
            shelf_close(comps, comps_shelf_fd)
        else:
            thecomps = None
        if subs != None:
            thesubs = {}
            for s in subs:
                thesubs[s] = subs[s]
            shelf_close(subs, subs_shelf_fd)
        else:
            thesubs = None
        if views != None:
            theviews = {}
            for v in views:
                theviews[v] = views[v].__dict__
            shelf_close(views, views)
        else:
            theviews = None

        contextdict = {"contextinfo":contextinfo, "contexts":thecontexts, "components":thecomps, "views":theviews, "subs":thesubs}
        if level == None:
            return json.dumps(contextdict)
        else:
            return contextdict

    def import_model(self, 
        context=[], 
        partial_model=None):
        """Import a model

        :param context: context to import partial model to if None, use root of model
        :param partial_model: 
            - string containing JSON representation of model dictionary OR
            - a dictionary with elements:
                - contextinfo - Description, Identifier, perms, resolver
                - contexts - sub contexts
                - components
                - views
                - subs
        
        :return:
        
        :raise:
        """
        self.curcontext = self._getcontextdir(context)
        contextinfo = self.getcontext(context)
        perms = contextinfo['perms']
        if self.usertype != 'owner':
            if not (self.user in perms):
                raise ValueError("No permission for: %s in %s/%s" % (self.user, context, view))
        if self.usertype == 'app':
            if not self.checkpermission(context=context, componentid=None, app=self.user, permname='tell', permval=True):
                raise ValueError("No permission for: %s in %s/%s" % (self.user, context, view))
            
        if partial_model == None:
            return
        if isinstance(partial_model, basestring):
            newmodel = json.loads(partial_model)
        else:
            newmodel = partial_model
        cinfo = newmodel['contextinfo']
        newcontext = context+[cinfo['Identifier']]
        if not self.existcontext(newcontext):
            con = Context(Identifier=cinfo['Identifier'], Description=cinfo['Description'], resolver=cinfo['resolver'], perms=cinfo['perms'])
            self.mkcontext(context=context, contextobj=con)
        else:
            logging.debug("%s exists",newcontext)
        for compname, comp in newmodel['components'].items():
            newcobj = Component()
            for k,v in comp.items():
                #print "comp items:", k, v
                if k not in ["evidencelist","value"]:
                    newcobj.__dict__[k] = v
            self.mkcomponent(newcontext, newcobj)
            comp["evidencelist"].reverse()
            for ev in comp["evidencelist"]:
                evv = Evidence(evidence_type="explicit") # evidence type will be overwritten by imported evidence
                for k,v in ev.items():
                    evv.__dict__[k] = v
                logging.debug("=>> tell %s %s %s", newcontext, compname, evv.__dict__)
                self.tell(context=newcontext, componentid=compname, evidence=evv, dosubs=False)
        for viewname, view in newmodel['views'].items():
            newview = View()
            for k,v in view.items():
                newview.__dict__[k] = v
            try:
                self.mkview(newcontext, newview)
            except:
                logging.debug( "View exists: %s %s", newcontext, newview)
            logging.debug( ">>VIEW %s %s", viewname, view)
        for subname, sub in newmodel['subs'].items():
            for k,v in sub.items():
                logging.debug( ">>SUB %s %s %s", subname, k, v)
                self.subscribe(context=newcontext, view=[subname], subscription=v)
        if newmodel['contexts'] != None:
            for contextname, cont in newmodel['contexts'].items():
                logging.debug( ">>CONTEXT %s %s", contextname, cont)
                self.import_model(newcontext, cont)
        
        return newmodel
    
    def tell(self, 
        context=[],
        componentid=None,
        evidence=None,   # evidence obj
        dosubs=True):
        """Tell the model something

        :param context: a list giving the path to the required context
        :param componentid: identifier of the component
        :param evidence: (:class:`Evidence`) object to add to the component
        :return:
        :raise:
        """
        logging.debug('context: %s, componentid %s, evidence %s, dosubs %s', repr(context), repr(componentid), repr(evidence), dosubs)
        if componentid == None:
            raise ValueError("tell: component id is None")
        if evidence == None:
            raise ValueError("tell: no evidence provided")
        if not isinstance(componentid, basestring):
            raise ValueError("tell: component id is not string type")
        self.curcontext = self._getcontextdir(context)
        contextinfo = self.getcontext(context)
        logging.debug('contextinfo %s',contextinfo)
        perms = contextinfo['perms']
        if self.usertype != 'owner':
            if not (self.user in perms):
                raise ValueError("No permission for: %s in %s" % (self.user, context))
        if self.usertype == 'app':
            if not self.checkpermission(context=context, componentid=None, app=self.user, permname='tell', permval=True):
                raise ValueError("No permission for: %s in %s/%s" % (self.user, context, componentid))
        comps,comps_shelf_fd = shelf_open(self.curcontext+"/.components", "w")

        if componentid in comps:
            evidence.creation_time = time.time()
            evidence.owner = self.user
            cobj = comps[componentid]
            if cobj.value_type == "enum":
                if evidence.value not in cobj.value_list:
                    raise ValueError("tell: value '%s' not in value list %s for component '%s' of type 'enum'" % (evidence.value, repr(cobj.value_list), componentid))
            try:
                evdb,evdb_fd = shelf_open(self.curcontext+"/.evidence", "w")
            except:
                raise ValueError("tell: no evidence db for %s"%(self.curcontext))
            if componentid not in evdb:
                raise ValueError("tell: no evidence db entry for %s"%(componentid))
            evcount = evdb[componentid]+1
            evdb[componentid] = evcount
            evidence.source = self.user
            evdb["%s:%d"%(componentid,evcount)] = evidence
            shelf_close(evdb, evdb_fd)
            if dosubs:
                self.checksubs(context, componentid)
        else:
            raise ValueError("tell: component id %s not found"%(componentid))
        shelf_close(comps, comps_shelf_fd)
        return None

    def set_goals(self, 
        context=[],
        componentid=None,
        goals=None):
        """set the goal list for a component. requires "tell" permission

        :param context: a list giving the path to the required context
        :param componentid: identifier of the component
        :param goals: list of goal component paths
        :return:
        :raise:
        """
        if componentid == None:
            raise ValueError("set_goals: component id is None")
        if goals == None:
            raise ValueError("set_goals: no goal list provided")
        self.curcontext = self._getcontextdir(context)
        contextinfo = self.getcontext(context)
        perms = contextinfo['perms']
        if self.usertype != 'owner':
            if self.user not in perms:
                raise ValueError("No permission for: %s in %s" % (self.user, context))
        if self.usertype == 'app':
            if not self.checkpermission(context=context, componentid=None, app=self.user, permname='tell', permval=True):
                raise ValueError("No permission for: %s in %s/%s" % (self.user, context, componentid))
        comps,comps_shelf_fd = shelf_open(self.curcontext+"/.components", "w")
        if componentid in comps:
            cobj = comps[componentid]
        else:
            raise ValueError("set_goals: component id %s not found"%(componentid))
        cobj.goals = goals
        comps[componentid] = cobj
        shelf_close(comps, comps_shelf_fd)
        return None

    def checksubs(self, context, componentid):
        """check subscriptions for componentid in current context. implemented in active

        :param context: a list giving the path to the required context
        :param componentid: identifier of the component
        :return:
        :raise:
        """
        pass
    
    def getcontext(self, context=[], getsize=False):
        """
        :param context: a list giving the path to the required context
        :return: a dictionary containing information associated with the context
        :raise:
        """
        def getcontextsize(dir="."):
            size = 0
            dir += "/"
            for f in glob.glob(dir+".*") + glob.glob(dir+"*"):
                if os.path.isdir(f):
                    size += getcontextsize(f)
                else:
                    size += os.stat(f).st_size
            return size

        try:
            contextdb,contextdb_shelf_fd = shelf_open(self._getcontextdir(context)+"/.context", "r")
        except:
            return {} # root context - FIX
        contextinfo = {}
        for k in contextdb:
            contextinfo[k] = contextdb[k]
        shelf_close(contextdb, contextdb_shelf_fd)
        if getsize:
            contextinfo['size'] = getcontextsize(self._getcontextdir(context))

        logging.debug('Context is %s', contextinfo)
        return contextinfo

    def setcontext(self, context=[], **kwargs):
        """Set the context

        :param context: a list giving the path to the required context 
        :param \*\*kwargs: a set of keyword arguments giving information to associate with the context

        :return:
            True on success
            False if the context doesn't exist
        """
        try:
            contextdb, contextdb_shelf_fd = shelf_open(self._getcontextdir(context)+"/.context", "w")
        except:
            return False
        for k,v in kwargs.items():
            contextdb[k] = v
        shelf_close(contextdb, contextdb_shelf_fd)
        return True


    def existcontext(self, context=[]):
        """
        :param context: a list giving the path to the required context 
    
        :return:
            True if context exists
            False if the context doesn't exist
        """
        return os.path.exists(self._getcontextdir(context)+"/.context")

    def mkcomponent(self, 
        context=[],
        componentobj=None):
        """Make a new component in a given context

        :param context: a list giving the path to the required context 
        :param componentobj: (:class:`Component`) a Component object with the context
        :return:
            None on success
            a string error message on error
        """
        if componentobj == None:
            return "component object is None"
        if componentobj.value != None:
            return "component value specified as %s at creation - not allowed"%(componentobj.value)
        self.curcontext = self._getcontextdir(context)
        comps, comps_shelf_fd = shelf_open(self.curcontext+"/.components", "w")
        if componentobj.Identifier in comps:
            return "component %s already exists"%(componentobj.Identifier)
        comps[componentobj.Identifier] = componentobj
        shelf_close(comps, comps_shelf_fd)
        try:
            evdb,evdb_fd = shelf_open(self.curcontext+"/.evidence", "w")
        except:
            raise ValueError("mkcomponent: no evidence db for %s"%(self.curcontext))
        if componentobj.Identifier in evdb:
            raise ValueError("mkcomponent: evidence db entry for %s already present"%(componentid))
        evdb[componentobj.Identifier] = 0
        shelf_close(evdb, evdb_fd)
        return None # all ok

    def delcomponent(self,
        context= [],
        componentid=None):
        """Delete an existing component in a given context
        
        :param context: a list giving the path to the required context 
        :param id: the id for a componen
        
        :return:
            None on success
            a string error message on error
        """
        if componentid == None:
            return "no component specified for deletion"
        self.curcontext = self._getcontextdir(context)
        comps, comps_shelf_fd = shelf_open(self.curcontext+"/.components", "w")
        if componentid in comps:
            del comps[componentid]
        else:
            return "no component matched %s"%(componentid)

        shelf_close(comps, comps_shelf_fd)
        try:
            evdb,evdb_fd = shelf_open(self.curcontext+"/.evidence", "w")
        except:
            raise ValueError("delcomponent: no evidence db for %s"%(self.curcontext))
        if componentid not in evdb:
            raise ValueError("mkcomponent: no evidence db entry for %s "%(componentid))
        evcount = evdb[componentid]
        for evcount in range(evdb[componentid]):
            del evdb["%s:%d"%(componentid, evcount+1)]
        del evdb[componentid]
        shelf_close(evdb, evdb_fd)
        return None # all ok

    def registerapp(self, app=None, desc="", password=None, realm='password'):
        """registers a password for an app
        
        :param app: app name is a string (needs checking TODO)
        :param desc: the app description string
            app passwords are stored at the top level .model db
        :param realm: The type of access method. 'oauth' if it's an app (like mneme or umbrowser) that
            can handle oauth. 'password' for the old password system.
        
        :return: returns a dictionary containing description and password(access key). If 'password' realm was requested, but
            no password given, returns None
        """
        if realm == 'password' and password is None:
            return None
        if self.usertype != 'owner':
            raise ValueError("registerapp: must be owner to set password for %s" % (app))
        p = hashlib.md5()
        if password is None:
            password = ''
        p.update(password)
        if app not in self.moddb['apps']:
            self.moddb['apps'][app] = {}
        self.moddb['apps'][app]['description'] = desc
        self.moddb['apps'][app]['realm'] = realm
        self.moddb['apps'][app]['password'] = p.hexdigest()

        mod, mod_shelf_fd = shelf_open(os.path.join(self.modeldir,self.modelname,".model"), "w")
        mod['apps'] = self.moddb['apps']
        shelf_close(mod, mod_shelf_fd)
        a = self.moddb['apps'][app]
        a['givenpw'] = self.password
        return a

    def deleteapp(self, app=None):
        """deletes an app
        """
        if app not in self.moddb['apps']:
            raise ValueError("deleteapp: app %s not registered"%(app))
        if self.usertype != 'owner':
            raise ValueError("deleteapp: must be owner to delete app %s" % (app))
        del self.moddb['apps'][app]
        mod, mod_shelf_fd = shelf_open(os.path.join(self.modeldir,self.modelname,".model"), "w")
        mod['apps'] = self.moddb['apps']
        shelf_close(mod, mod_shelf_fd)

    def listapps(self):
        """returns an dictionary of apps that are registered
            key is app name, 'description' is app description
        """
        apps = {}

        for app in self.moddb['apps']:
            apps[app] = {}
            apps[app]['description'] = self.moddb['apps'][app]['description']
        return apps

    def setpermission(self, context=None, componentid=None, app=None, permissions={}):
        """sets ask/tell permission for a context (if componentid is None) or
                a component
        """
        if self.usertype != "owner":
            raise ValueError("must be model owner to set permissions")
        if componentid == None:
            try:
                contextdb,contextdb_shelf_fd = shelf_open(self._getcontextdir(context)+"/.context", "w")
            except:
                raise ValueError("setpermission: no context db for %s"%(context))
            perms = contextdb['perms']
            if app not in self.moddb['apps']:
                raise ValueError("setpermission: app %s not registered"%(app))
            if app not in perms:
                perms[app] = {}
            for k,v in permissions.items():
                perms[app][k] = v
            contextdb['perms'] = perms
            shelf_close(contextdb, contextdb_shelf_fd)
            

    def getpermission(self, context=None, componentid=None, app=None):
        """gets permissions for a context (if componentid is None) or a component # not implemented yet ####
        
        :return: a tuple (ask,tell)
        """
        logging.debug('getperms: context %s, comp %s, app %s', repr(context), repr(componentid), app)
        if app not in self.moddb['apps']:
            raise ValueError("getpermission: app %s not registered"%(app))
        if componentid == None:
            try:
                contextdb,contextdb_shelf_fd = shelf_open(self._getcontextdir(context)+"/.context", "r")
            except:
                raise ValueError("getpermission: no context db for %s"%(context))
            perms = contextdb['perms']
            shelf_close(contextdb, contextdb_shelf_fd)
            return perms.get(app)

    def checkpermission(self, context=None, componentid=None, app=None, permname=None, permval=None):
        """gets permissions for a context (if componentid is None) or a component # not implemented ####
        :return:
            True is the app has the nominated permission
            False if not
        """
        perms = self.getpermission(context=context, componentid=componentid, app=app)
        if permname in perms:
            return permval == perms[permname]
        return False

    def setcomponentoption(self, context, componentid, **kwargs):
        """

        :param context: a list giving the path to the required context 
        :param componentid: name of the component to set items on
        :param \*\*kwargs: a set of keyword arguments giving information to associate with the component
    
        :return:
            True on success
            False if the component doesn't exist
        """
        ok = False
        # try:
        if True:
            comps, comps_shelf_fd = shelf_open(self._getcontextdir(context)+"/.components", "w")
            if componentid in comps:
                comp = comps[componentid]
                for k,v in kwargs.items():
                    comp.__dict__[k] = v
                comps[componentid] = comp
            shelf_close(comps, comps_shelf_fd)
            ok = True
        try:
            pass
        except:
            
            try:
                shelf_close(comps, comps_shelf_fd)
            except:
                pass
        return ok

    def setresolver(self, context, componentid, resolver):
        return self.setcomponentoption(context,componentid,resolver=resolver)

    def getresolvers(self):
        return list(self.resolverlist.keys())

    def mkcontext(self, 
        context= [],
        contextobj=None):
        """Make a new context in a given context

        :param context: a list giving the path to the context that will hold the new context 
        :param contextobj: a Context object
        
        :return: True if created ok, False otherwise
        """
        self.curcontext = self._getcontextdir(context)
        self.curcontext += "/"+contextobj.Identifier
        try:
            os.mkdir(self.curcontext)
        except:
            return False
        con, con_shelf_fd = shelf_open(self.curcontext+"/.context", "c")
        for k,v in contextobj.__dict__.items():
            con[k] = v
        shelf_close(con, con_shelf_fd)
        comps, comps_shelf_fd = shelf_open(self.curcontext+"/.components", "c")
        shelf_close(comps, comps_shelf_fd)
        evdb,evdb_fd = shelf_open(self.curcontext+"/.evidence", "c")
        shelf_close(evdb, evdb_fd)
        views, views_shelf_fd = shelf_open(self.curcontext+"/.views", "c")
        shelf_close(views, views_shelf_fd)
        subs, subs_shelf_fd = shelf_open(self.curcontext+"/.subscriptions", "c")
        shelf_close(subs, subs_shelf_fd)
        return True

    def delcontext(self,
        context=[]):
        """Delete a context
        """
        okchars = string.ascii_letters+string.digits+'_'
        for c in context:
            ok = False not in [x in okchars for x in list(c)]
            if not ok:
                raise ValueError('bad character in context name')
        ctxtdir = [self.modelname]+context
        delcontext = ctxtdir[-1]  # directory to remove
        
        try:
            ctxtbase = [self.modeldir] + ctxtdir
            ctxtbase = ctxtbase[:-1]
            #print ">>> chdir ", os.path.join(*ctxtbase)
            os.chdir(os.path.join(*ctxtbase))
        except:
            return False
        
        #import tarfile, time
        #tarname = "%s-%s.tgz" % (time.strftime("%Y%m%d%H%M", time.localtime()), delcontext)
        #print ">>> ", tarname
        #tar = tarfile.open(os.path.join(*[self.modeldir, tarname]), "w:gz")
        #tar.add(delcontext)
        #tar.close()

        #print '>>> os.system("rm -rf ' + os.path.join(*([self.modeldir]+ctxtdir))+'"'
        os.system("rm -rf "+os.path.join(*([self.modeldir]+ctxtdir)))
        return True

    def mkview(self, 
        context= [],
        viewobj=None):
        """Make a new view in a given context

        :param context: a list giving the path to the required context 
        :param viewobj: a View object
        """
        if viewobj == None:
            raise ValueError('view object is None')
        view_id = viewobj.Identifier
        self.curcontext = self._getcontextdir(context)
        views, views_shelf_fd = shelf_open(self.curcontext+"/.views", "w")
        if view_id in views:
            raise ValueError("view %s already exists"%(viewobj.Identifier))
        views[view_id] = viewobj
        shelf_close(views, views_shelf_fd)
        return None

    def delview(self,
        context=[],
        viewid=None):
        """Delete an existing view within a given context

        :param context: a list giving the path to the required context 
        :param viewid: view identifier
    
        :return:
            on success, None
            on failure, a string reporting the problem
        """
        if viewid == None:
            return "no view specified for deletion"
        self.curcontext = self._getcontextdir(context)
        views, views_shelf_fd = shelf_open(self.curcontext+"/.views", "w")
        if viewid in views:
            del views[viewid]
        else:
            return "no view matched $s"%(viewid)
        shelf_close(views, views_shelf_fd)
        return None # all ok

    def _getcontextdir(self, context):
        if context == None:
            context = []
        if isinstance(context, basestring):
            context = [x for x in context.split(os.sep) if x not in ['','.','..']]
        if not (type(context) is ListType):
            raise ValueError("Context <%s> is wrong type"%(context))
        ctxt = [self.modeldir, self.modelname]+context
        return os.path.join(*ctxt)

