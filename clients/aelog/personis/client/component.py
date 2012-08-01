import time

ComponentTypes = ["attribute", "activity", "knowledge", "belief", "preference", "goal"]
ValueTypes = ["string", "number", "boolean", "enum", "JSON"]

class Component:
    """ component object
        Identifier  the identifier of the component
                unique in the context
        Description readable description
        creation_time   time of creation of the component
        component_type  ["attribute", "activity", "knowledge", "belief", "preference", "goal"]
        value_type  ["string", "number","boolean", "enum", "JSON"]
        value_list    a list of strings that are the possible values for type "enum"
        value       the resolved value
        resolver    default resolver for this component
        goals       list of component paths eg [ ['Personal', 'Health', 'weight'], ...]
        evidencelist    list of evidence objects
    """
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
        if not self.component_type in ComponentTypes:
            raise TypeError, "bad component type %s"%(self.component_type)
        if not self.value_type in ValueTypes:
            raise ValueError, "bad component value definition %s"%(self.value_type)
        if (self.value_type == "enum") and (len(self.value_list) == 0):
            raise ValueError, "type 'enum' requires non-empty value-list"
        if self.value != None:
            if (self.value_type == "enum") and not (self.value in self.value_list):
                raise ValueError, "value '%s' not in value_list for type 'enum'" % (self.value)