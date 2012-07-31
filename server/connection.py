
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
