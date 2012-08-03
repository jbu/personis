import httplib2

class Connection(object):

    def __init__(self, uri = None, credentials = None, http = None):
        self.http = http
        self.credentials = credentials
        self.uri = uri
        self.authorized = False

    def valid(self):
        if self.uri == None or self.credentials == None:
            return False
        return True

    def get_http(self):
        if self.http == None:
            self.http = httplib2.Http()
        if not self.authorized:
            self.credentials.authorize(self.http)
            self.authorized = True
        return self.http

    def __repr__(self):
        return 'uri: %s, credentials: %s'%(self.uri, self.credentials.to_json())