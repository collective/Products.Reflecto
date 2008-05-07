from zope.interface import implements

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from ZPublisher.Iterators import filestream_iterator

from Products.CMFCore.DynamicType import DynamicType
from Products.CMFCore.permissions import View
from Products.Reflecto.interfaces import IReflectoFile
from Products.Reflecto.content.proxy import BaseProxy
from Products.Reflecto.config import HAS_CACHESETUP


class ReflectoFile(BaseProxy, DynamicType):
    """A filesystem reflected file."""

    __implements__ = (BaseProxy.__implements__, DynamicType.__implements__)

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

        from Products.CMFCore.utils import getToolByName
        from Products.CacheSetup.config import CACHE_TOOL_ID
        from Products.CacheSetup.cmf_utils import _setCacheHeaders

        # The CacheSetup API is not just weird. It's insane.

        pcs=getToolByName(self, CACHE_TOOL_ID, None)
        if pcs is None or not pcs.getEnabled():
            return

        request=getattr(self, "REQUEST", None)
        if request is None:
            return

        member=pcs.getMember()
        rule=self.getReflector().getCacheRule()
        rule=getattr(pcs.getRules(), rule, None)
        if rule is None:
            return
        # We have to pretend that the default view is being accessed,
        # otherwise the rule will refuse to find a header set.
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
        
        RESPONSE.setHeader('Last-Modified', self.Date())
        RESPONSE.setHeader('Content-Type', self.Format())
        RESPONSE.setHeader('Content-Length', len(iterator))
        
        return iterator

 
    security.declareProtected(View, "index_html")
    def index_html(self):
        """Download the file"""
        return self()


    security.declareProtected(View, "SearchableText")
    def SearchableText(self):
        """Return textual content of the file for the search index.
        
        This is only used If TextIndexNG3 is not installed.
        """
        result = BaseProxy.SearchableText(self)
        if self.Format().startswith("text/"):
            result += ' ' + self.get_data()

        return result
    

InitializeClass(ReflectoFile)

