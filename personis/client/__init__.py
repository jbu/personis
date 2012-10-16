'''
.. module:: personis.client
   :platform: Unix, Windows
   :synopsis: Client for the personis user model server
'''

__docformat__ = "restructuredtext en"

import time
import httplib2
from util import *
import logging

class Connection(object):
    """Connection object

    Contains the state of your connection to personis.

    :param uri: The uri of a personis server.
    :param credentials: (:class:`httplib2.Credentials`) Credentails for connecting to the server.
    :param http: (:class:`httplib2.Http`) An http connection to use.

    .. Note::
        Http can be used if you need to configure proxies etc.
        The class needs either uri or credentials to work.
    """

    def __init__(self, uri = None, credentials = None, http = None):
        self.http = http
        self.credentials = credentials
        self.uri = uri
        self.authorized = False

    def valid(self):
        """Is this valid?

        :returns:  boolean -- is valid.
         """
        if self.uri == None or self.credentials == None:
            return False
        return True

    def get_http(self):
        """Get the http connection given in the construction, or in set_http
 
        :returns: :class:`httplib2.Http`
        """
        if self.http == None:
            self.http = httplib2.Http()
        if not self.authorized:
            self.credentials.authorize(self.http)
            self.authorized = True
        return self.http

    def set_http(self, http):
        """Set the http connection to use

        :param http: The http connection to use
        :type http: :class:`httplib2.Http` 
        """
        self.http = http
        self.authorized = False

    def __repr__(self):
        return 'uri: %s, credentials: %s'%(self.uri, self.credentials.to_json())

class Evidence:
    """ evidence object

    :param evidence_type: (:class:`EvidenceTypes`) - The type of the evidencelist
    :param source: (str) A string indicating the source of the evidence
    :param value: (object) - Any python object
    :param comment: (str) - string with extra information about the evidence
    :param flags: (list) -   a list of strings eg "goal"
    :param time: (integer) -    notional creation time optionally given by user
    :param creation_time: (integer) - actual time evidence item was created
    :param useby: (integer) -   timestamp evidence expires (if required)
    """

    EvidenceTypes = ["explicit", "implicit", "exmachina", "inferred", "stereotype"] 
    """Evidence can be:

    - explicit: given by the user  (given)
    - implicit: observed by the machine (observation)
    - exmachina: told (to the user) by the machine (told)
    - inferred: evidence generated by inference (external or internal)
    - stereotype: evidence added by a stereotype
    """

    def __init__(self, **kargs):

        self.flags = []
        self.evidence_type = None
        self.source = None
        self.owner = None
        self.value = None
        self.comment = None
        self.creation_time = None
        self.time = None  
        self.useby = None
        self.objectType = "Evidence"
        for k,v in kargs.items():
            self.__dict__[k] = v
        if not self.evidence_type in Evidence.EvidenceTypes:
            raise TypeError, "bad evidence type %s"%(self.evidence_type)

    def __str__(self):
        return 'evidence: '+repr(self.__dict__)

class View:
    """view object

    :param Identifier: The identifier of the component - unique in the context.
    :type Identifier: str
    :param Description: Readable description
    :type Description: str
    :param component_list: List of components in the view
    :type component_list: list
    :return:
    """
    def __init__(self, **kargs):

        self.Identifier = None
        self.Description = ""
        self.component_list = None
        self.objectType = "View"
        for k,v in kargs.items():
            self.__dict__[k] = v
        if self.Identifier == None:
            return None

class Context:
    """ context object

    :param Identifier: The identifier of the component - unique in the context.
    :param Description: Readable description
    :param resolver: default resolver for components in this context
    """ 

    def __init__(self, **kargs):

        self.Identifier = None
        self.Description = ""
        self.perms = {} # permissions - owner only to begin
        self.resolver = None
        self.objectType = "Context"
        self.creation_time = time.time()
        for k,v in kargs.items():
            self.__dict__[k] = v
        if self.Identifier == None:
            return None

    def __str__(self):
        return 'Identifier {}, Description {}, perms {}'.format(self.Identifier, self.Description, self.perms)

class Component:
    """ component object

    :param Identifier: (string) - The identifier of the component - unique in the context.
    :param Description: (string) - Readable description
    :param creation_time: (string) - time of creation of the component.
    :param component_type: (list) - ["attribute", "activity", "knowledge", "belief", "preference", "goal"]
    :param value_type: (list) - ["string", "number","boolean", "enum", "JSON"]
    :param value_list: (list) - a list of strings that are the possible values for type "enum".
    :param value: (string) - the resolved value.
    :param resolver: (string) - default resolver for this component.
    :param goals: (list) - list of component paths eg [ ['Personal', 'Health', 'weight'], ...]
    :param evidencelist: (list) - list of evidence objects.
    """

    ComponentTypes = ["attribute", "activity", "knowledge", "belief", "preference", "goal"]
    ValueTypes = ["string", "number", "boolean", "enum", "JSON"]

    def __init__(self, **kargs):

        # set some default values
        self.Identifier = None
        self.Description = ""
        self.component_type = None
        self.value_type = None
        self.value_list = []
        self.value = None
        self.resolver = None
        self.goals = []
        self.evidencelist = []
        self.objectType = "Component"
        self.creation_time = time.time()
        for k,v in kargs.items():
            self.__dict__[k] = v
        if self.Identifier == None:
            return None
        if not self.component_type in Component.ComponentTypes:
            raise TypeError, "bad component type %s"%(self.component_type)
        if not self.value_type in Component.ValueTypes:
            raise ValueError, "bad component value definition %s"%(self.value_type)
        if (self.value_type == "enum") and (len(self.value_list) == 0):
            raise ValueError, "type 'enum' requires non-empty value-list"
        if self.value != None:
            if (self.value_type == "enum") and not (self.value in self.value_list):
                raise ValueError, "value '%s' not in value_list for type 'enum'" % (self.value)

    def __str__(self):
        return 'Component: '+ repr(self.__dict__)

class Access(object):
    """Client version of access for client/server system

    :param model: (string) - model name. If none, then default user model. ('-' maps to the model of the authenticated user)
    :param connection: (Connection) - Connection to use connecting to server. If none, you need to provide a URI or credentials
    :param uri: (string) - URI of personis server. Need either this or credentials, or a connection.
    :param credentials: (Credentials) - Credentials for a connection (if no connection or URI provided.)
    :param http: (httplib2.Http) - Http connection to use.
    :param loglevel: (int) - Configure logging.
    :param test: (boolean) - default to true. If false, the test connection to the server is not done, for speed if connections are established repeatedly.

    """

    def __init__(self, model = '-', connection=None, uri = None, credentials = None, http = None, loglevel=logging.INFO, test=True):

        if connection == None:
            connection = Connection(uri, credentials, http)    
        self.modelname = model
        self.user = ''
        self.password = ''
        self.connection = connection
        if http != None:        
            self.connection.set_http(http)
            
        ok = False

        if not test: 
            return
        try:
            logging.info("jsondocall: access %s", self.connection)
            ok = do_call("access", {}, self.connection)
            logging.info("---------------------- result returned %s", ok)
        except:
            logging.debug(traceback.format_exc())
            raise ValueError, "cannot access model"
        if not ok:
            raise ValueError, "server cannot access model"

    def ask(self,
            context=[],
            view=None,
            resolver=None,
            showcontexts=None):

        """Ask personis for some information

        :param context: (list) - The path of context identifiers
        :param view: (list or string) - either:
            - an identifier of a view in the context specified
            - a list of component identifiers or full path lists
            - None indicating that the values of all components in the context be returned
        :param resolver: (string) - specifies a resolver, default is the builtin resolver

        :return: a list of matched components
        """
        reslist = do_call("ask", {'modelname':self.modelname,\
                                    'user':self.user,\
                                    'password':self.password,\
                                    'context':context,\
                                    'view':view,\
                                    'resolver':resolver,\
                                    'showcontexts':showcontexts},
                                    self.connection)
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

    def tell(self,
            context=[],
            componentid=None,
            evidence=None):   # evidence obj

        """Tell the model something.

        :param context: a list giving the path to the required context
        :param componentid: identifier of the component
        :param evidence: evidence object to add to the component
        :return: None on success or a string error message on error
        :raise:
        """
        if componentid == None:
            raise ValueError, "tell: componentid is None"
        if evidence == None:
            raise ValueError, "tell: no evidence provided"

        return do_call("tell", {'modelname':self.modelname,\
            'user':self.user,\
            'password':self.password,\
            'context':context,\
            'componentid':componentid,\
            'evidence':evidence.__dict__},
            self.connection
        )

    def mkcomponent(self,
            context=[],
            componentobj=None):
        """Make a new component in a given context

        :param context: a list giving the path to the required context
        :param componentobj: a Component object
        :return: None on success or a string error message on error
        :raise:
        """
        if componentobj == None:
            raise ValueError, "mkcomponent: componentobj is None"
        return do_call("mkcomponent", {'modelname':self.modelname,\
                                        'user':self.user,\
                                        'password':self.password,\
                                        'context':context,\
                                        'componentobj':componentobj.__dict__},
                                        self.connection)
    def delcomponent(self,
            context=[],
            componentid=None):
        """Delete an existing component in a given context

        :param context: a list giving the path to the required context
        :param componentid: the id for a component
        :return: None on success or a string error message on error
        :raise:
        """
        if componentid == None:
            raise ValueError, "delcomponent: componentid is None"
        return do_call("delcomponent", {'modelname':self.modelname,\
                                        'user':self.user,\
                                        'password':self.password,\
                                        'context':context,\
                                        'componentid':componentid},
                                        self.connection)
    def delcontext(self,
            context=[]):
        """Delete an existing context

        :param context: a list giving the path to the required context
        :return: None on success or a string error message on error
        :raise:
        """
        if context == None:
            raise ValueError, "delcontext: context is None"
        return do_call( "delcontext", {'modelname':self.modelname,\
                                        'user':self.user,\
                                        'password':self.password,\
                                        'context':context},
                                        self.connection)
    def getresolvers(self):
        '''Return a list of the available resolver names'''
        return do_call("getresolvers", {'modelname':self.modelname,\
                                        'user':self.user, 'password':self.password},
                                        self.connection)

    def setresolver(self,
            context,
            componentid,
            resolver):
        """set the resolver for a given component in a given context

        :param context: a list giving the path to the required context
        :param componentid: the id for a given component
        :param resolver: the id of the resolver
        :return: None on success or a string error message on error
        :raise:
        """
        if componentid == None:
            raise ValueError, "setresolver: componentid is None"
        return do_call("setresolver", {'modelname':self.modelname,\
                                        'user':self.user,\
                                        'password':self.password,\
                                        'context':context,\
                                        'componentid':componentid, \
                                        'resolver':resolver},
                                        self.connection)

    def mkview(self,
            context=[],
            viewobj=None):
        """Make a new view in a given context

        :param context: a list giving the path to the required context
        :param viewobj: a View object

        :return: None on success or a string error message on error
        """
        if viewobj == None:
            raise ValueError, "mkview: viewobj is None"
        return do_call("mkview", {'modelname':self.modelname,\
                                    'user':self.user,\
                                    'password':self.password,\
                                    'context':context,\
                                    'viewobj':viewobj.__dict__},
                                    self.connection)
    def delview(self,
            context=[],
            viewid=None):
        """Delete an existing view in a given context

        :param context: a list giving the path to the required context
        :param viewid: the id for the view
        :return: None on success or a string error message on error
        """
        if viewid == None:
            raise ValueError, "delview: viewid is None"
        return do_call("delview", {'modelname':self.modelname,\
                                    'user':self.user,\
                                    'password':self.password,\
                                    'context':context,\
                                    'viewid':viewid},
                                    self.connection)


    def mkcontext(self,
            context= [],
            contextobj=None):
        """Make a new context in a given context

        :param context: a list giving the path to the required context
        :param contextobj: a Context object
        :return: None on success or a string error message on error
        """
        if contextobj == None:
            raise ValueError, "mkcontext: contextobj is None"
        return do_call("mkcontext", {'modelname':self.modelname,\
                                    'user':self.user,\
                                    'password':self.password,\
                                    'context':context,\
                                    'contextobj':contextobj.__dict__},
                                    self.connection)


    def getcontext(self,
            context=[],
            getsize=False):
        """Get context information

        :param context: - a list giving the path to the required context
        :param getsize: - True if the size in bytes of the context subtree is required
        :return: A context, or a string error message on error
        """
        return do_call("getcontext", {'modelname':self.modelname,\
                                        'user':self.user,\
                                        'password':self.password,\
                                        'context':context,\
                                        'getsize':getsize},
                                        self.connection)

    def subscribe(self,
            context=[],
            view=None,
            subscription=None):
        """

        :param context: is a list giving the path of context identifiers
        :param view: is either:
            an identifier of a view in the context specified
            a list of component identifiers or full path lists
            None indicating that the values of all components in the context be returned
        :param subscription: is a Subscription object
        :return: None on success or a string error message on error
        """
        return  do_call("subscribe", {'modelname':self.modelname,\
                                        'user':self.user,\
                                        'password':self.password,\
                                        'context':context,\
                                        'view':view,\
                                        'subscription':subscription},
                                        self.connection)
    def delete_sub(self,
            context=[],
            componentid=None,
            subname=None):
        """

        :param context: is a list giving the path of context identifiers
        :param componentid: designates the component subscribed to
        :param subname: is the subscription name
        :return: None on success or a string error message on error
        """
        return  do_call("delete_sub", {'modelname':self.modelname,\
                                        'user':self.user,\
                                        'password':self.password,\
                                        'context':context,\
                                        'componentid':componentid,\
                                        'subname':subname},
                                        self.connection)

    def export_model(self,
            context=[],
            resolver=None):
        """

        :param context: is the context to export
        :param resolver: 
            - is a string containing the name of a resolver or
            - resolver is a dictionary containing information about resolver(s) to be used and arguments::

                the "resolver" key gives the name of a resolver to use, if not present the default resolver is used
                the "evidence_filter" key specifies an evidence filter
                eg 'evidence_filter' =  "all" returns all evidence,
                                        "last10" returns last 10 evidence items,
                                        "last1" returns most recent evidence item,
                                        None returns no evidence
        :return: A json model dump or a string error message on error
        """
        return do_call("export_model", {'modelname':self.modelname,\
                                        'user':self.user,\
                                        'password':self.password,\
                                        'context':context,\
                                        'resolver':resolver},
                                        self.connection)

    def import_model(self,
            context=[],
            partial_model=None):
        """

        :param context: is the context to import into
        :param partial_modeL: is a json encoded string containing the partial model
        :return: None on success or a string error message on error
        """
        return do_call("import_model", {'modelname':self.modelname,\
                                        'user':self.user,\
                                        'password':self.password,\
                                        'context':context,\
                                        'partial_model':partial_model},
                                        self.connection)
    def set_goals(self,
            context=[],
            componentid=None,
            goals=None):
        """

        :param context: is a list giving the path of context identifiers
        :param componentid: designates the component with subscriptions attached
        :param goals: is a list of paths to components that are:
            - goals for this componentid if it is not of type goal
            - components that contribute to this componentid if it is of type goal
        :return: None on success or a string error message on error
        """
        return  do_call("set_goals", {'modelname':self.modelname,
                                        'user':self.user,
                                        'password':self.password,
                                        'context':context,
                                        'componentid':componentid,
                                        'goals':goals},
                                        self.connection)


    def list_subs(self,
            context=[],
            componentid=None):
        """

        :param context: is a list giving the path of context identifiers
        :param componentid: designates the component with subscriptions attached

        :return: A list of subscriptions or a string error message on error
        """
        return  do_call("list_subs", {'modelname':self.modelname,
                                        'user':self.user,
                                        'password':self.password,
                                        'context':context,
                                        'componentid':componentid},
                                        self.connection)

    def registerapp(self, app=None, desc="", password=None, realm='password'):
        """registers a password for an app

        :param app: name is a string (needs checking TODO)
        :param desc: (str) description of app
        :param password: app passwords are stored at the top level .model db

        :return: None on success or a string error message on error
        """
        return do_call("registerapp", {'modelname':self.modelname,
                                        'user':self.user,
                                        'password':self.password,
                                        'app':app,
                                        'realm':realm,
                                        'description':desc,
                                        'apppassword':password},
                                        self.connection)

    def deleteapp(self, app=None):
        """deletes an app

        :return: None on success or a string error message on error
        """
        if app == None:
            raise ValueError, "deleteapp: app is None"
        return do_call("deleteapp", {'modelname':self.modelname,
                                        'user':self.user,
                                        'password':self.password,
                                        'app':app},
                                        self.connection)

    def listapps(self):
        """returns array of registered app names

        :return: A list of apps or a string error message on error
        """
        return do_call("listapps", {'modelname':self.modelname,
                                        'user':self.user,
                                        'password':self.password},
                                        self.connection)

    def setpermission(self, context=None, componentid=None, app=None, permissions={}):
        """sets ask/tell permission for a context (if componentid is None) or a component

        :return: None on success or a string error message on error
        """
        return do_call("setpermission", {'modelname':self.modelname,\
                                        'user':self.user,\
                                        'password':self.password,\
                                        'context': context,\
                                        'componentid': componentid,\
                                        'app': app,\
                                        'permissions': permissions},
                                        self.connection)

    def getpermission(self, context=None, componentid=None, app=None):
        """gets permissions for a context (if componentid is None) or a component

        :return: a tuple (ask,tell) on success or a string error message on error
        """
        return do_call("getpermission", {'modelname':self.modelname,\
                                       'user':self.user,\
                                       'password':self.password,\
                                       'context': context,\
                                       'componentid': componentid,\
                                       'app': app},
                                       self.connection)