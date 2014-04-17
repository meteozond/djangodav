# Portions (c) 2014, Alexander Klimenko <alex@erix.ru>
# All rights reserved.
#
# Copyright (c) 2011, SmartFile <btimby@smartfile.com>
# All rights reserved.
#
# This file is part of DjangoDav.
#
# DjangoDav is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DjangoDav is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with DjangoDav.  If not, see <http://www.gnu.org/licenses/>.
from hashlib import md5

from django.utils.http import urlquote
from djangodav.utils import rfc3339_date, rfc1123_date


class BaseDavResource(object):
    ALL_PROPS = ['getcontentlength', 'creationdate', 'getlastmodified', 'resourcetype', 'displayname']

    LIVE_PROPERTIES = [
        '{DAV:}getetag', '{DAV:}getcontentlength', '{DAV:}creationdate',
        '{DAV:}getlastmodified', '{DAV:}resourcetype', '{DAV:}displayname'
    ]

    def __init__(self, path):
        self.path = []
        path = path.strip("/")
        if path:
            self.path = path.split("/")

    def get_path(self):
        path = [urlquote(p) for p in self.path]
        return ("/" if path else "") + "/".join(path) + ("/" * self.is_collection)

    def get_displaypath(self):
        return ("/" if self.path else "") + "/".join(self.path) + ("/" * (self.is_collection))

    @property
    def displayname(self):
        if not self.path:
            return None
        return self.path[-1]

    def get_parent_path(self):
        path = self.path[:-1]
        return "/" + "/".join(path) + "/" if path else ""

    def get_parent(self):
        return self.__class__(self.get_parent_path())

    def get_descendants(self, depth=1, include_self=True):
        """Return an iterator of all descendants of this resource."""
        if include_self:
            yield self
        # If depth is less than 0, then it started out as -1.
        # We need to keep recursing until we hit 0, or forever
        # in case of infinity.
        if depth != 0:
            for child in self.get_children():
                for desc in child.get_descendants(depth=depth-1, include_self=True):
                    yield desc

    @property
    def getcontentlength(self):
        raise NotImplementedError()

    @property
    def creationdate(self):
        """Return the create time as rfc3339_date."""
        return rfc3339_date(self.get_created())

    @property
    def getlastmodified(self):
        """Return the modified time as http_date."""
        return rfc1123_date(self.get_modified())

    def get_created(self):
        """Return the create time as datetime object."""
        raise NotImplementedError()

    def get_modified(self):
        """Return the modified time as datetime object."""
        raise NotImplementedError()

    @property
    def getetag(self):
        raise NotImplementedError()

    def copy(self,  destination, depth=0):
        raise NotImplementedError()

    def move(self,  destination):
        raise NotImplementedError()

    def write(self, content):
        raise NotImplementedError()

    def read(self):
        raise NotImplementedError()

    @property
    def is_collection(self):
        raise NotImplementedError()

    @property
    def is_object(self):
        raise NotImplementedError()

    @property
    def exists(self):
        raise NotImplementedError()

    def get_children(self):
        raise NotImplementedError()

    def delete(self):
        raise NotImplementedError()

    def create_collection(self):
        raise NotImplementedError()


class MetaEtagMixIn(object):
    @property
    def getetag(self):
        """Calculate an etag for this resource. The default implementation uses an md5 sub of the
        absolute path modified time and size. Can be overridden if resources are not stored in a
        file system. The etag is used to detect changes to a resource between HTTP calls. So this
        needs to change if a resource is modified."""
        hashsum = md5()
        hashsum.update(self.displayname)
        hashsum.update(str(self.creationdate))
        hashsum.update(str(self.getlastmodified))
        hashsum.update(str(self.getcontentlength))
        return hashsum.hexdigest()
