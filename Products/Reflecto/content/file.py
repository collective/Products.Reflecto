import mimetypes
from zope.interface import implements

from AccessControl import ClassSecurityInfo
try:
    from App.class_init import InitializeClass
except ImportError:
    from Globals import InitializeClass
from ZPublisher.Iterators import filestream_iterator
from webdav.Resource import Resource

from Products.CMFCore.DynamicType import DynamicType
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import getToolByName

from Products.Reflecto.interfaces import IReflectoFile
from Products.Reflecto.content.proxy import BaseProxy, BaseMove
from Products.Reflecto.config import HAS_CACHESETUP
from Products.Reflecto.permissions import AddFilesystemObject

from ZServer import LARGE_FILE_THRESHOLD
from App.Common import rfc1123_date
from stat import ST_MTIME

import os
import os.path
import tempfile


class ReflectoFile(BaseMove, Resource, BaseProxy, DynamicType):
    """A filesystem reflected file."""

    implements(IReflectoFile)

    meta_type = "ReflectoFile"
    portal_type = "ReflectoFile"

    security = ClassSecurityInfo()

    security.declareProtected(View, "get_data")
    def get_data(self):
        # Just to be more compatible with a standard file type
        return self.getFileContent()


    security.declareProtected(View, "getFileContent")
    def getFileContent(self):
        return open(self.getFilesystemPath(), "rb").read()
    

    security.declarePrivate(View, "setCacheHeaders")
    def setCacheHeaders(self):
        if not HAS_CACHESETUP:
            return

        from Products.CacheSetup.config import CACHE_TOOL_ID
        from Products.CacheSetup.cmf_utils import _setCacheHeaders

        # The CacheSetup API is not just weird. It's insane.

        pcs=getToolByName(self, CACHE_TOOL_ID, None)
        if pcs is None or not pcs.getEnabled():
            return

        request=getattr(self, "REQUEST", None)
        if request is None:
            return

        rule=self.getReflector().getCacheRule()
        if not rule:
            return

        rule=getattr(pcs.getRules(), rule, None)
        if rule is None:
            return
        # We have to pretend that the default view is being accessed,
        # otherwise the rule will refuse to find a header set.
        member=pcs.getMember()
        header_set=rule.getHeaderSet(request, self, "reflecto_file_view",
                                     member)
        if header_set is None:
            return

        expr_context=rule._getExpressionContext(request, self,
                            "reflecto_file_view", member, keywords={})

        _setCacheHeaders(self, {}, rule, header_set, expr_context)


    def __call__(self):
        """Download the file"""
        self.setCacheHeaders()
        RESPONSE=self.REQUEST['RESPONSE']
        iterator = filestream_iterator(self.getFilesystemPath(), 'rb')
        
        RESPONSE.setHeader('Last-Modified', rfc1123_date(self.getStatus()[ST_MTIME]))
        RESPONSE.setHeader('Content-Type', self.Format())
        RESPONSE.setHeader('Content-Length', len(iterator))
        
        return iterator

 
    security.declareProtected(View, "index_html")
    def index_html(self):
        """Download the file"""
        return self()


    def Format(self):
        extension=os.path.splitext(self.getId().lower())[1]
        type=None

        mtr=getToolByName(self, "mimetypes_registry", None)
        if mtr is not None:
            mimetype=mtr.lookupExtension(extension[1:])
            if mimetype is None:
                mimetype=mtr.classify(self.getFileContent())

            if mimetype is not None:
                return mimetype.normalized()

        try:
            return mimetypes.types_map[extension]
        except KeyError:
            return "application/octet-stream"


    security.declareProtected(View, "SearchableText")
    def SearchableText(self):
        """Return textual content of the file for the search index.
        
        This is only used If TextIndexNG3 is not installed.
        """
        result = BaseProxy.SearchableText(self)
        if self.Format().startswith("text/"):
            result += ' ' + self.get_data()

        return result
    
    security.declareProtected(AddFilesystemObject, 'PUT')
    def PUT(self, REQUEST, RESPONSE):
        """Handle HTTP PUT requests"""
        self.dav__init(REQUEST, RESPONSE)
        self.dav__simpleifhandler(REQUEST, RESPONSE, refresh=1)
        file=REQUEST['BODYFILE']
        path = self.getFilesystemPath()
        
        if isinstance(file, tempfile._TemporaryFileWrapper):
            # Zope >= 2.11
            # If we only ran on unix we would use os.link here. Instead, rename
            # the file and manually close the NamedTemporaryFile, bypassing the
            # call to os.unlink.
            os.rename(file.name, path)
            os.chmod(path, 0644)
            file.file.close()
            file.close_called = True
        else:
            # Zope < 2.11        
            try:
                # For OSes which support it (Windows) we need to use the
                # O_BINARY flag to prevent cr/lf rewriting.
                # os.O_EXCL not used so uploads can overwrite existing files
                flags=os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_BINARY
            except AttributeError:
                flags=os.O_WRONLY|os.O_CREAT|os.O_TRUNC
            fd=os.open(self.getFilesystemPath(), flags, 0644)
            
            data = file.read(LARGE_FILE_THRESHOLD) # 512k chunks, might be optimal...
            while data:
                os.write(fd, data)
                data = file.read(LARGE_FILE_THRESHOLD)
            os.close(fd)         
            
        self.indexObject()



InitializeClass(ReflectoFile)

