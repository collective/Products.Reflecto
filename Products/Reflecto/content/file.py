from zope.interface import implements

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from ZPublisher.Iterators import filestream_iterator

from Products.CMFCore.DynamicType import DynamicType
from Products.CMFCore.permissions import View
from Products.Reflecto.interfaces import IReflectoFile
from Products.Reflecto.content.proxy import BaseProxy


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
    

    def __call__(self):
        """Download the file"""
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

