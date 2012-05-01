import errno
import os
import shutil
import stat
from types import StringType
from UserDict import DictMixin

from Acquisition import aq_base, aq_inner, aq_parent
from AccessControl import ClassSecurityInfo, getSecurityManager
from AccessControl.Permissions import copy_or_move
from AccessControl.Permissions import access_contents_information
try:
    from App.class_init import InitializeClass
except ImportError:
    from Globals import InitializeClass
from OFS.CopySupport import CopyError, _cb_decode, _cb_encode, cookie_path
from OFS.CopySupport import copy_re
from OFS.event import ObjectWillBeMovedEvent, ObjectWillBeRemovedEvent
from OFS.event import ObjectClonedEvent
from OFS.Moniker import Moniker, loadMoniker
from OFS.ObjectManager import checkValidId, BadRequestException
from zExceptions import BadRequest, Unauthorized
from ZODB.POSException import ConflictError
from webdav.Collection import Collection

from zope.event import notify
from zope.interface import implements, Interface
from zope.component import queryMultiAdapter
from zope.app.container.contained import notifyContainerModified
from zope.app.container.contained import ObjectMovedEvent, ObjectRemovedEvent
from zope.lifecycleevent import ObjectCopiedEvent

from Products.CMFCore.DynamicType import DynamicType
from Products.CMFCore.permissions import View, DeleteObjects
from Products.CMFPlone.interfaces.constrains import IConstrainTypes
from Products.statusmessages.interfaces import IStatusMessage

from Products.Reflecto.permissions import AddFilesystemObject
from Products.Reflecto.interfaces import IReflectoDirectory
from Products.Reflecto.interfaces import ILifeProxy
from Products.Reflecto.interfaces import IReflectoProxy
from Products.Reflecto.interfaces import IReflector
from Products.Reflecto.content.proxy import BaseProxy, BaseMove
from Products.Reflecto.content.file import ReflectoFile
from Products.Reflecto.utils import addMarkerInterface

from ZPublisher import xmlrpc
from webdav.NullResource import NullResource

def _getViewFor(context):
        return context.reflector_view


class ReflectoDirectoryBase:
    implements(IReflectoDirectory, IConstrainTypes)
    
    security = ClassSecurityInfo()

    isPrincipiaFolderish = True
    
    security.declarePrivate('acceptableFilename')
    def acceptableFilename(self, name):
        """Check if a filename is allowed."""
        try:
            checkValidId(self, name, True)
        except BadRequest:
            return False
        if name.startswith('@@') or name[0] == '.':
            return False
        return True

    security.declarePrivate('acceptableFile')
    def acceptableFile(self, name):
        """Check if the file is of an acceptable type.

        We need to ignore devices and sockes.
        """
        try:
            mode=os.stat(name)[stat.ST_MODE]
            return stat.S_ISDIR(mode) or stat.S_ISREG(mode)
        except OSError:
            pass
        return False


    # IReadContainer implementation based on DictMixin
    def __getitem__(self, key):
        if not self.has_key(key):            
            raise KeyError(key)
        
        filename = os.path.join(self.getFilesystemPath(), key)
        if os.path.isdir(filename):
            class_ = ReflectoDirectory
        else:
            class_ = ReflectoFile
            
        path = self.getPathToReflectoParent() + (key,)
        obj = class_(path).__of__(self)

        if self.getReflector().getLife():
            addMarkerInterface(obj, ILifeProxy)

        return obj
    

    def __iter__(self):
        try:
            path = self.getFilesystemPath()
        except AttributeError:
            # No acquisition context, fail silently
            raise StopIteration
        
        try:
            for name in os.listdir(path):
                if not self.acceptableFilename(name):
                    continue
                if not self.acceptableFile(os.path.join(path, name)):
                    continue
                yield name
        except OSError, e:
            if e.errno==errno.ENOENT:
                raise StopIteration
            raise
            
    def keys(self):
        return list(self.__iter__())
            
    def has_key(self, key):
        if not isinstance(key, basestring):
            return False

        if not self.acceptableFilename(key):
            return False
        
        try:
            filename = os.path.join(self.getFilesystemPath(), key)
        except AttributeError:
            # No acquisition context, fail silently
            return False
            
        return os.path.exists(filename)
    
    # Acquisition wrappers don't support the __iter__ slot, so re-implement
    # iteritems to call __iter__ directly.
    def iteritems(self):
        for k in self.__iter__():
            yield (k, self[k])
    
########################################################################
# ObjectManager implementation
    security.declareProtected(access_contents_information,
                              'objectIds')
    def objectIds(self, spec=None):
        # Returns a list of subobject ids of the current object.
        # If 'spec' is specified, returns objects whose meta_type
        # matches 'spec'.
        assert spec is None, 'spec argument unsupported'
        return self.__iter__()


    security.declareProtected(access_contents_information,
                              'objectValues')
    def objectValues(self, spec=None):
        # Returns a list of actual subobjects of the current object.
        # If 'spec' is specified, returns only objects whose meta_type
        # match 'spec'.
        assert spec is None, 'spec argument unsupported'
        return self.itervalues()


    security.declareProtected(access_contents_information,
                              'objectItems')
    def objectItems(self, spec=None):
        # Returns a list of (id, subobject) tuples of the current object.
        # If 'spec' is specified, returns only objects whose meta_type match
        # 'spec'
        assert spec is None, 'spec argument unsupported'
        return self.iteritems()


########################################################################
# WebDAV implementation

    def MKCOL_handler(self,id,REQUEST=None,RESPONSE=None):
        """
            Handle WebDAV MKCOL.
        """
        if not self.acceptableFilename(id):
            raise BadRequestException, ('The id "%s" is invalid.' % id)
        path = os.path.join(self.getFilesystemPath(), id)
        os.mkdir(path, 0775)

        dir = self.aq_inner[id]
        dir.indexObject()
    
    def _checkId(self, id, allow_dup=0):
        if not allow_dup and self.has_key(id):
            raise BadRequestException, ('The id "%s" is invalid--'
                                        'it is already in use.' % id)
        if not self.acceptableFilename(id):
            raise BadRequestException, ('The id "%s" is invalid.' % id)
    
    def _verifyObjectPaste(self, obj, validate_src=1):
        # validate_src ignored
        assert isinstance(obj, BaseProxy)
        prefix = os.path.commonprefix((obj.getFilesystemPath(),
                                       self.getFilesystemPath()))
        if prefix == obj.getFilesystemPath():
            raise CopyError, "This object cannot be pasted into itself"
        sman = getSecurityManager()
        if not sman.checkPermission(AddFilesystemObject, self):
            raise CopyError, 'Insufficient Privileges'
     
########################################################################
# IConstrainTypes implementation

    def getConstrainTypesMode(self):
        return 1

    def getLocallyAllowedTypes(self):
        return []

    def getImmediatelyAddableTypes(self):
        return []

    def getDefaultAddableTypes(self):
        return []

    def allowedContentTypes(self):
        return []
    
########################################################################
# Deletion support

    security.declareProtected(DeleteObjects, 'manage_delObjects')
    def manage_delObjects(self, ids=[], REQUEST=None):
        """Delete reflected files or directories
        
        The objects specified in 'ids' get deleted. This emulates the
        ObjectManager interface enough to support deletion in Plone only.
        When file removal fails, errors are communicated through the return
        of the successful ids and the IStatusMessage utility
        
        """
        if type(ids) is StringType:
            ids = [ids]
        if not ids:
            raise ValueError('No items specified')
        
        # To avoid inconsistencies, first test file availability
        for id in ids:
            if not self.has_key(id):
                raise KeyError(id)
            notify(ObjectWillBeRemovedEvent(self[id], self, id))
            
        problem_ids = []
        path = self.getFilesystemPath()
        for id in ids:
            subpath = os.path.join(path, id)
            ob = self[id]
            try:
                if os.path.isdir(subpath):
                    shutil.rmtree(subpath)
                else:
                    os.unlink(subpath)
                notify(ObjectRemovedEvent(ob, self, id))
            except OSError:
                problem_ids.append(id)
                    
        if problem_ids:
            sm = IStatusMessage(getattr(self, 'REQUEST', None), None)
            if sm is not None:
                sm.addStatusMessage(
                    'Failed to remove some files: %s' % problem_ids, 'stop')
                
        if set(ids) - set(problem_ids):
            indexview = self.unrestrictedTraverse('@@index')
            indexview.index()
            notifyContainerModified(self)
        
        return problem_ids or None # None expected by webdav on success
    
########################################################################
# Renaming support

    security.declareProtected(copy_or_move, 'manage_renameObjects')
    def manage_renameObjects(self, ids=[], new_ids=[]):
        """Rename reflected files or directories
        
        The objects specified in 'ids' get renamed to 'new_ids'. This emulates 
        the CopyContainer interface enough to support renaming in Plone only.
        When file renaming fails, errors are communicated through the return
        of the successful ids and the IStatusMessage utility
        
        """
        if len(ids) != len(new_ids):
            raise BadRequest('Please rename each listed object.')
        if not ids:
            raise ValueError('No items specified')
        
        # To avoid inconsistencies, first test file availability
        for old, new in zip(ids, new_ids):
            if not self.has_key(old):
                raise KeyError(old)
            if not self.acceptableFilename(new) or self.has_key(new):
                raise CopyError, 'Invalid Id'
            notify(ObjectWillBeMovedEvent(self[old], self, old, self, new))
            
        problem_ids = []
        path = self.getFilesystemPath()
        for id in ids:
            try:
                os.rename(os.path.join(path, old), os.path.join(path, new))
                notify(ObjectMovedEvent(self[new], self, old, self, new))
            except OSError:
                problem_ids.append(old)
                    
        if problem_ids:
            sm = IStatusMessage(getattr(self, 'REQUEST', None), None)
            if sm is not None:
                sm.addStatusMessage(
                    'Failed to rename some files: %s' % problem_ids, 'stop')
                
        if set(ids) - set(problem_ids):
            indexview = self.unrestrictedTraverse('@@index')
            indexview.index()
            notifyContainerModified(self)
        
        return list(set(ids) - set(problem_ids))
    
########################################################################
# Copying support
# This re-implements much of CopyContainer, and is only intended to work
# with Plone
    
    def cb_dataValid(self):
        try:
            _cb_decode(self.REQUEST['__cp'])
        except:
            return False
        return True
    
    def _generate_copy_id(self, id):
        n = 0
        old = id
        match = copy_re.match(id)
        if match:
            n = int(match.group(1) or '1')
            old = match.group(2)
        while True:
            if not self.has_key(id):
                return id
            id = 'copy%s_of_%s' % (n and n + 1 or '', old)
            n += 1
            
    def _generate_cp_cookie(self, ids, flag, REQUEST=None):
        if type(ids) is StringType:
            ids=[ids]
            
        try:
            oblist = [Moniker(self[id]).dump() for id in ids]
        except KeyError:
            # Plone expects attribute errors here
            raise AttributeError
        cp = _cb_encode((flag, oblist))
        
        if REQUEST is not None:
            resp = REQUEST['RESPONSE']
            resp.setCookie('__cp', cp, path=cookie_path(REQUEST))
            REQUEST['__cp'] = cp
        return cp
    
    security.declareProtected(copy_or_move, 'manage_copyObjects')
    def manage_copyObjects(self, ids=None, REQUEST=None, RESPONSE=None):
        """Put a reference to the objects named in ids in the clip board"""
        return self._generate_cp_cookie(ids, 0, REQUEST)

    security.declareProtected(copy_or_move, 'manage_cutObjects')
    def manage_cutObjects(self, ids, REQUEST=None):
        """Put a reference to the objects named in ids in the clip board"""
        return self._generate_cp_cookie(ids, 1, REQUEST)
    
    security.declareProtected(copy_or_move, 'manage_pasteObjects')
    def manage_pasteObjects(self, cp):
        """Paste previously copied objects into the current object."""
        op, mdatas = _cb_decode(cp)
        COPY = op == 0 # Otherwise its a paste operation
        
        # Copy or paste always fails without write permission here
        sman = getSecurityManager()
        if not sman.checkPermission(AddFilesystemObject, self):
            raise CopyError, 'Insufficient Privileges'
        
        oblist = []
        app = self.getPhysicalRoot()
        
        # Loading and security checks
        for mdata in mdatas:
            m = loadMoniker(mdata)
            try:
                ob = m.bind(app)
            except ConflictError:
                raise
            except:
                raise CopyError, 'Item not found'
            if not IReflectoProxy.providedBy(ob) or IReflector.providedBy(ob):
                raise CopyError, 'Cannot paste into this object'
            parent = aq_parent(aq_inner(ob))
            if not sman.validate(None, parent, None, ob):
                raise Unauthorized(ob.getId())
            if not COPY:
                if not sman.checkPermission(DeleteObjects, parent):
                    raise Unauthorized('Delete not allowed')
                prefix = os.path.commonprefix((ob.getFilesystemPath(),
                                               self.getFilesystemPath()))
                if prefix == ob.getFilesystemPath():
                    raise CopyError, "This object cannot be pasted into itself"
            oblist.append(ob)

        result = []
        problem_ids = []
        path = self.getFilesystemPath()
        for ob in oblist:
            old = ob.getId()
            new = self._generate_copy_id(old)
            result.append(dict(id=old, new_id=new))
            oldpath = ob.getFilesystemPath()
            newpath = os.path.join(path, new)
            
            if COPY:
                try:
                    if IReflectoDirectory.providedBy(ob):
                        shutil.copytree(oldpath, newpath)
                    else:
                        shutil.copy2(oldpath, newpath)
                    notify(ObjectCopiedEvent(self[new], ob))
                    notify(ObjectClonedEvent(self[new]))
                except EnvironmentError:
                    problem_ids.append(result.pop())
            else:
                # paste/move
                oldparent = aq_parent(aq_inner(ob))
                notify(ObjectWillBeMovedEvent(ob, oldparent, old, self, new))
                
                if aq_base(self) is aq_base(oldparent):
                    # No need to move from self to self
                    result[-1]['new_id'] = old
                    # Original CopyContainer does emit events for this case
                    notify(ObjectMovedEvent(ob, self, old, self, old))
                    continue
                
                try:
                    shutil.move(oldpath, newpath)
                    indexview = oldparent.unrestrictedTraverse('@@index')
                    indexview.index()
                    notify(ObjectMovedEvent(self[new], oldparent, old, self,
                                            new))
                    notifyContainerModified(oldparent)
                except EnvironmentError:
                    if os.path.exists(newpath):
                        # partial move
                        try:
                            if os.path.isdir(newpath):
                                shutil.rmtree(newpath)
                            else:
                                os.unlink(newpath)
                        except EnvironmentError:
                            pass # Really weird access issues, time to bail
                    problem_ids.append(result.pop())
                
        if problem_ids:
            sm = IStatusMessage(getattr(self, 'REQUEST', None), None)
            if sm is not None:
                sm.addStatusMessage(
                    'Failed to copy or paste some files: %s' % problem_ids,
                    'stop')
                
        if result:
            indexview = self.unrestrictedTraverse('@@index')
            indexview.index()
            notifyContainerModified(self)
        
        return result

# mix in selected methods from DictMixin
# We don't want *everything* because some cause problems for us
for m in ('__contains__', 'iterkeys', 'itervalues', 'values', 'items', 'get'):
    setattr(ReflectoDirectoryBase, m, getattr(DictMixin, m).im_func)
    
InitializeClass(ReflectoDirectoryBase)

class ReflectoDirectory(ReflectoDirectoryBase, BaseMove, Collection, BaseProxy, DynamicType):
    """A filesystem directory."""

    meta_type = "ReflectoDirectory"
    portal_type = "ReflectoDirectory"

    security = ClassSecurityInfo()

    def __call__(self):
        """ Invokes the default view.
        """
        ti = self.getTypeInfo()
        method_id = ti and ti.queryMethodID('(Default)', context=self)
        if method_id and method_id!='(Default)':
            method = getattr(self, method_id)
        else:
            method = _getViewFor(self)

        if getattr(aq_base(method), 'isDocTemp', 0):
            return method(self, self.REQUEST, self.REQUEST['RESPONSE'])
        else:
            return method()


    security.declareProtected(View, "index_html")
    def index_html(self):
        """Download the file"""
        return self()


    security.declareProtected(View, 'view')
    def view(self):
        """ Returns the default view even if index_html is overridden.
        """
        return self()
    
    def __bobo_traverse__(self, REQUEST, name):
        try:
            return self[name]
        except KeyError:
            pass
            
        if hasattr(aq_base(self), name):
            return getattr(self, name)
        
        # webdav
        method = REQUEST.get('REQUEST_METHOD', 'GET').upper()
        if (method not in ('GET', 'POST') and not
              isinstance(REQUEST.RESPONSE, xmlrpc.Response) and
              REQUEST.maybe_webdav_client and not REQUEST.path):
            return ReflectoNullResource(self, name, REQUEST).__of__(self)
        
        # try to find a view
        subobject = queryMultiAdapter((self, REQUEST), Interface, name)                
        if subobject is not None:
            return subobject.__of__(self)
        
        # finally try acquired objects
        return getattr(self, name)

InitializeClass(ReflectoDirectory)


class ReflectoNullResource(NullResource):
    security = ClassSecurityInfo()
    
    security.declarePublic('PUT')
    def PUT(self, REQUEST, RESPONSE):
        """Create a new non-collection resource.
        """
        self.dav__init(REQUEST, RESPONSE)

        name = self.__name__
        parent = self.__parent__

        # Locking not implemented.
        
        if not self.acceptableFilename(name):
            raise BadRequestException, ('The id "%s" is invalid.' % name)
        
        path = parent.getPathToReflectoParent() + (name,)
        obj = ReflectoFile(path).__of__(parent)

        if self.getReflector().getLife():
            addMarkerInterface(obj, ILifeProxy)
        
        # Security is checked here.
        obj.PUT(REQUEST, RESPONSE)

        RESPONSE.setStatus(201)
        RESPONSE.setBody('')
        return RESPONSE
    
InitializeClass(ReflectoNullResource)
