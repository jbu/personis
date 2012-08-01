class Context:
    """ context object
        Identifier  the identifier of the component
                unique in the context
        Description readable description
        resolver    default resolver for components in this context
    """
    def __init__(self, **kargs):
        # set some default values
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