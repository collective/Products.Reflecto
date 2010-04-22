import os
import os.path
import shutil
import sys
from stat import ST_CTIME, ST_MTIME, ST_SIZE

import Acquisition
from Acquisition import aq_base, aq_parent, aq_inner
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import copy_or_move
from DateTime import DateTime
try:
    from App.class_init import InitializeClass
except ImportError:
    from Globals import InitializeClass
from OFS.CopySupport import CopyError
from OFS.SimpleItem import Item

from zope.interface import implements
from zope.event import notify
from zope.app.container.contained import ObjectMovedEvent
from zope.app.container.contained import notifyContainerModified
from zope.lifecycleevent import ObjectCopiedEvent
from OFS.event import ObjectWillBeMovedEvent, ObjectClonedEvent
from zExceptions import MethodNotAllowed
from zExceptions import BadRequest
from zExceptions import Forbidden
from zExceptions import NotFound
from zExceptions import Unauthorized
from webdav.interfaces import IWriteLock
from webdav import Lockable
from webdav.common import PreconditionFailed
from webdav.common import Locked
from webdav.common import Conflict

from Products.CMFCore.permissions import View
from Products.CMFCore.interfaces import ICatalogableDublinCore
from Products.CMFCore.interfaces import IDublinCore
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware

from Products.Reflecto.interfaces import IReflector
from Products.Reflecto.interfaces import IReflectoProxy
from Products.Reflecto.interfaces import IReflectoDirectory

# The system default timezone
system_timezone = DateTime().timezone()


def indexWrapper(cls, method):
    method=getattr(cls, method)

    def wrapper(self, *args, **kwargs):
        reflector=self.getReflector()
        if aq_base(reflector) is not aq_base(self) and reflector.getLife():
            return
        return method(self, *args, **kwargs)

    return wrapper


class BaseProxy(CMFCatalogAware, Item, Acquisition.Implicit):
    meta_type="Reflecto proxy"

    implements(IReflectoProxy, IDublinCore, ICatalogableDublinCore)

    security = ClassSecurityInfo()
    
    _path = ()

    def __init__(self, path):
        self.id=path[-1]
        self._path=path

    # Wrap indexing methods to make sure objects are not in the catalog
    # when running the reflecto in life mode. Note that we do not wrap
    # unindexObject - unindexing can never be a bad thing in this situation.
    indexObject = indexWrapper(CMFCatalogAware, "indexObject")
    reindexObject = indexWrapper(CMFCatalogAware, "reindexObject")
    reindexObjectSecurity = indexWrapper(CMFCatalogAware, "reindexObjectSecurity")

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

    def _deleteOwnershipAfterAdd(self):
        # Modified version of AccessControler.Owned, which does not
        # recurse into children.

        # Only delete _owner if it is an instance attribute.
        if self.__dict__.get('_owner', _mark) is not _mark:
            del self._owner

        

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
        return self._statTime(ST_MTIME).ISO8601()


    def CreationDate(self, zone=None):
        # Not all operating systems and file systems keep track of a creation
        # date. If this is not supported this will return the last modification
        # date instead.
        return self._statTime(ST_CTIME).ISO8601()


    def ModificationDate(self, zone=None):
        return self._statTime(ST_MTIME).ISO8601()


    def Type(self):
        return self.meta_type


    def Identifier(self):
        return self.absolute_url()


    def Format(self):
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
        reflex = self.getReflector().aq_base

        if container.aq_base is reflex:
            return

        if IReflectoProxy.providedBy(container) and \
                container.getReflector().aq_base is reflex:
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
    
    @property
    def _p_mtime(self):
        # used by webdav HEAD
        # properties are not acquisition wrapped, so self._stat must already
        # exist. For webdav it already is, but elsewhere be careful
        return self.getStatus()[ST_MTIME]

InitializeClass(BaseProxy)


class BaseMove:
    security = ClassSecurityInfo()

    security.declareProtected(copy_or_move, 'COPY')
    def COPY(self, REQUEST, RESPONSE):
        """Create a duplicate of the source resource. This is only allowed
        within the same reflecto directory."""
        self.dav__init(REQUEST, RESPONSE)
        if not hasattr(aq_base(self), 'cb_isCopyable') or \
           not self.cb_isCopyable():
            raise MethodNotAllowed, 'This object may not be copied.'

        depth=REQUEST.get_header('Depth', 'infinity')
        if not depth in ('0', 'infinity'):
            raise BadRequest, 'Invalid Depth header.'

        dest=REQUEST.get_header('Destination', '')
        while dest and dest[-1]=='/':
            dest=dest[:-1]
        if not dest:
            raise BadRequest, 'Invalid Destination header.'

        try: path = REQUEST.physicalPathFromURL(dest)
        except ValueError:
            raise BadRequest, 'Invalid Destination header'

        name = path.pop()

        oflag=REQUEST.get_header('Overwrite', 'F').upper()
        if not oflag in ('T', 'F'):
            raise BadRequest, 'Invalid Overwrite header.'

        try: parent=self.restrictedTraverse(path)
        except ValueError:
            raise Conflict, 'Attempt to copy to an unknown namespace.'
        except NotFound:
            raise Conflict, 'Object ancestors must already exist.'
        except:
            t, v, tb=sys.exc_info()
            raise t, v
        if hasattr(parent, '__null_resource__'):
            raise Conflict, 'Object ancestors must already exist.'
        existing=hasattr(aq_base(parent), name)
        if existing and oflag=='F':
            raise PreconditionFailed, 'Destination resource exists.'
        try:
            parent._checkId(name, allow_dup=1)
        except:
            raise Forbidden, sys.exc_info()[1]
        try:
            parent._verifyObjectPaste(self)
        except Unauthorized:
            raise
        except:
            raise Forbidden, sys.exc_info()[1]

        # Now check locks.  The If header on a copy only cares about the
        # lock on the destination, so we need to check out the destinations
        # lock status.
        ifhdr = REQUEST.get_header('If', '')
        if existing:
            # The destination itself exists, so we need to check its locks
            destob = aq_base(parent)._getOb(name)
            if IWriteLock.providedBy(destob) and destob.wl_isLocked():
                if ifhdr:
                    itrue = destob.dav__simpleifhandler(
                        REQUEST, RESPONSE, 'COPY', refresh=1)
                    if not itrue:
                        raise PreconditionFailed
                else:
                    raise Locked, 'Destination is locked.'
        elif IWriteLock.providedBy(parent) and parent.wl_isLocked():
            if ifhdr:
                parent.dav__simpleifhandler(REQUEST, RESPONSE, 'COPY',
                                            refresh=1)
            else:
                raise Locked, 'Destination is locked.'

        self._notifyOfCopyTo(parent, op=0)
        
        #### This part is reflecto specific
        if existing:
            object=getattr(parent, name)
            self.dav__validate(object, 'DELETE', REQUEST)
            parent.manage_delObjects([name])
        
        oldpath = self.getFilesystemPath()
        newpath = os.path.join(parent.getFilesystemPath(), name)
        
        if IReflectoDirectory.providedBy(self):
            if depth=='0':
                os.mkdir(newpath, 0775)
            else:
                shutil.copytree(oldpath, newpath)
        else:
            shutil.copy2(oldpath, newpath)
        ob = parent[name]
        ob.indexObject()
        notify(ObjectCopiedEvent(ob, self))
        notify(ObjectClonedEvent(ob))
        notifyContainerModified(parent)
        ####

        # We remove any locks from the copied object because webdav clients
        # don't track the lock status and the lock token for copied resources
        ob.wl_clearLocks()
        RESPONSE.setStatus(existing and 204 or 201)
        if not existing:
            RESPONSE.setHeader('Location', dest)
        RESPONSE.setBody('')
        return RESPONSE

    security.declareProtected(copy_or_move, 'MOVE')
    def MOVE(self, REQUEST, RESPONSE):
        """Move a resource to a new location within the reflector"""
        self.dav__init(REQUEST, RESPONSE)
        self.dav__validate(self, 'DELETE', REQUEST)
        if not hasattr(aq_base(self), 'cb_isMoveable') or \
           not self.cb_isMoveable():
            raise MethodNotAllowed, 'This object may not be moved.'

        dest=REQUEST.get_header('Destination', '')

        try: path = REQUEST.physicalPathFromURL(dest)
        except ValueError:
            raise BadRequest, 'No destination given'

        flag=REQUEST.get_header('Overwrite', 'F')
        flag=flag.upper()

        name = path.pop()
        parent_path = '/'.join(path)

        try: parent = self.restrictedTraverse(path)
        except ValueError:
            raise Conflict, 'Attempt to move to an unknown namespace.'
        except 'Not Found':
            raise Conflict, 'The resource %s must exist.' % parent_path
        except:
            t, v, tb=sys.exc_info()
            raise t, v
        if hasattr(parent, '__null_resource__'):
            raise Conflict, 'The resource %s must exist.' % parent_path
        existing=hasattr(aq_base(parent), name)
        if existing and flag=='F':
            raise PreconditionFailed, 'Resource %s exists.' % dest
        try:
            parent._checkId(name, allow_dup=1)
        except:
            raise Forbidden, sys.exc_info()[1]
        try:
            parent._verifyObjectPaste(self)
        except Unauthorized:
            raise
        except:
            raise Forbidden, sys.exc_info()[1]

        # Now check locks.  Since we're affecting the resource that we're
        # moving as well as the destination, we have to check both.
        ifhdr = REQUEST.get_header('If', '')
        if existing:
            # The destination itself exists, so we need to check its locks
            destob = aq_base(parent)._getOb(name)
            if IWriteLock.providedBy(destob) and destob.wl_isLocked():
                if ifhdr:
                    itrue = destob.dav__simpleifhandler(
                        REQUEST, RESPONSE, 'MOVE', url=dest, refresh=1)
                    if not itrue:
                        raise PreconditionFailed
                else:
                    raise Locked, 'Destination is locked.'
        elif IWriteLock.providedBy(parent) and parent.wl_isLocked():
            # There's no existing object in the destination folder, so
            # we need to check the folders locks since we're changing its
            # member list
            if ifhdr:
                itrue = parent.dav__simpleifhandler(REQUEST, RESPONSE, 'MOVE',
                                                    col=1, url=dest, refresh=1)
                if not itrue:
                    raise PreconditionFailed, 'Condition failed.'
            else:
                raise Locked, 'Destination is locked.'
        if Lockable.wl_isLocked(self):
            # Lastly, we check ourselves
            if ifhdr:
                itrue = self.dav__simpleifhandler(REQUEST, RESPONSE, 'MOVE',
                                                  refresh=1)
                if not itrue:
                    raise PreconditionFailed, 'Condition failed.'
            else:
                raise PreconditionFailed, 'Source is locked and no '\
                      'condition was passed in.'

        orig_container = aq_parent(aq_inner(self))
        orig_id = self.getId()

        self._notifyOfCopyTo(parent, op=1)

        #### This part is reflecto specific
        notify(ObjectWillBeMovedEvent(self, orig_container, orig_id,
                                      parent, name))
        self.unindexObject()
        if existing:
            object=parent[name]
            self.dav__validate(object, 'DELETE', REQUEST)
            parent.manage_delObjects([name])
            
        os.rename(self.getFilesystemPath(), os.path.join(parent.getFilesystemPath(), name))
        ob = parent[name]
        ob.indexObject()
        ####
        
        notify(ObjectMovedEvent(ob, orig_container, orig_id, parent, name))
        notifyContainerModified(orig_container)
        if aq_base(orig_container) is not aq_base(parent):
            notifyContainerModified(parent)

        RESPONSE.setStatus(existing and 204 or 201)
        if not existing:
            RESPONSE.setHeader('Location', dest)
        RESPONSE.setBody('')
        return RESPONSE
    

InitializeClass(BaseMove)
