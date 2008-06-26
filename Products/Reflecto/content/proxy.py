import mimetypes
import os.path
from stat import ST_CTIME, ST_MTIME, ST_SIZE

import Acquisition
from AccessControl import ClassSecurityInfo
from DateTime import DateTime
from Globals import InitializeClass
from OFS.CopySupport import CopyError
from OFS.SimpleItem import Item

from zope.interface import implements

from Products.CMFCore.permissions import View
from Products.CMFCore.interfaces import ICatalogableDublinCore
from Products.CMFCore.interfaces import IDublinCore
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware

from Products.Reflecto.interfaces import IReflector
from Products.Reflecto.interfaces import IReflectoProxy

# The system default timezone
system_timezone = DateTime().timezone()


class BaseProxy(CMFCatalogAware, Item, Acquisition.Implicit):
    meta_type="Reflecto proxy"

    implements(IReflectoProxy, IDublinCore, ICatalogableDublinCore)

    security = ClassSecurityInfo()
    
    _path = ()

    def __init__(self, path):
        self.id=path[-1]
        self._path=path


    security.declareProtected(View, "getReflector")
    def getReflector(self):
        """Return our Reflector object.
        """
        for parent in self.aq_inner.aq_chain:
            if parent is self.aq_base:
                continue
            if IReflector.providedBy(parent):
                return parent
            
        raise RuntimeError('Reflecto object cannot exist outside an IReflector '
                           'acquisition chain')

    security.declarePrivate('getPathToReflectoParent')
    def getPathToReflectoParent(self):
        """Return a path from the reflex object to this proxy.

        The path should be a tuple of strings.
        """
        return self._path

    security.declarePrivate('getFilesystemPath')
    def getFilesystemPath(self):
        """Return the filesystem path for this object.
        """
        return os.path.join(self.getReflector().getFilesystemPath(),
                                *self.getPathToReflectoParent())

    def __cmp__(self, other):
        try:
            return cmp(self.getPhysicalPath(), other.getPhysicalPath())
        except AttributeError:
            return cmp(id(self), id(other))
        
    def SearchableText(self):
        return self.Title()

########################################################################
# IDublinCore implementation

    security.declarePrivate('getStatus')
    def getStatus(self):
        """Return file status from our physical file.

        Since a stat(2) call is expensive on some operatin systems we cache
        the result.
        """
        if not hasattr(self, "_stat"):
            self._stat=os.stat(self.getFilesystemPath())
        return self._stat


    def _statTime(self, index, zone=None):
        if zone is None:
            zone=system_timezone
        return DateTime(self.getStatus()[index]).toZone(zone)


    def Title(self):
        return self.getId()


    def Description(self):
        return u""


    def Date(self, zone=None):
        return self._statTime(ST_MTIME).ISO()


    def CreationDate(self, zone=None):
        # Not all operating systems and file systems keep track of a creation
        # date. If this is not supported this will return the last modification
        # date instead.
        return self._statTime(ST_CTIME).ISO()


    def ModificationDate(self, zone=None):
        return self._statTime(ST_MTIME).ISO()


    def Type(self):
        return self.meta_type


    def Identifier(self):
        return self.absolute_url()


    def Format(self):
        try:
            return mimetypes.types_map[os.path.splitext(self.getId().lower())[1]]
        except KeyError:
            return "application/octet-stream"


########################################################################
# ICatalogableDublinCore implementation

    def created(self):
        return self._statTime(ST_CTIME)


    def modified(self):
        return self._statTime(ST_MTIME)



########################################################################
# ICopySource implementation

    def _notifyOfCopyTo(self, container, op=0):
        """Only allow copies to the same reflexion."""
        container = Acquisition.aq_inner(container)
        reflex = self.getReflector()

        if container is reflex:
            return

        if IReflectoProxy.providedBy(container) and \
                container.getReflector() is reflex:
            return

        # The exception we throw does not really matter; the CopyContainer
        # will only include the string version of the exception instance.
        # And further suckage: on error CopyContainer will redirect to user
        # to the ZMI. Gah.
        raise CopyError, (
            "It is not possible to copy or move a filesystem object "
            "outside of the containing reflex object.")

########################################################################
# other stuff

    get_content_type = Format
    getContentType = Format

    def get_size(self):
        return self.getStatus()[ST_SIZE]

InitializeClass(BaseProxy)
