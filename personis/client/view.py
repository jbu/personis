class View:
    """ view object
        Identifier  the identifier of the component
                unique in the context
        Description readable description
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