from Acquisition import aq_inner
from zope.interface import implements
try:
    from zope.app.i18n import ZopeMessageFactory as _
except ImportError:
    from zope.i18nmessageid import ZopeMessageFactory as _
from Products.Five import BrowserView
from Products.Reflecto.interfaces import IReflectoFile
from Products.Reflecto.interfaces import IReflectoDirectory
from Products.Reflecto.interfaces import IIndexView
from Products.CMFCore.utils import getToolByName

class IndexView(BrowserView):
    implements(IIndexView)

    def approve(self, obj):
        return not obj.getReflector().getLife()


    def unindex(self, proxy=None):
        if proxy is None:
            proxy=self.context

        ct=getToolByName(proxy, "portal_catalog")
        query=dict(path="/".join(proxy.getPhysicalPath()))

        proxypath="/".join(proxy.getPhysicalPath())
        for brain in ct.searchResults(query):
            if brain.getPath()!=proxypath:
                ct.uncatalog_object(brain.getPath())


    def index(self, proxy=None):
        if proxy is None:
            proxy=aq_inner(self.context)

        if not self.approve(proxy):
            return

        if IReflectoDirectory.providedBy(proxy):
            self.unindex(proxy)
            for (id, entry) in proxy.iteritems():
                if IReflectoDirectory.providedBy(entry):
                    self.index(entry)
                elif IReflectoFile.providedBy(entry):
                    entry.indexObject()

        proxy.indexObject()


    def __call__(self):
        self.index()

        pt=getToolByName(self.context, "plone_utils")
        pt.addPortalMessage(_(u"Reflector (re)indexed"))
        return self.request.response.redirect(self.context.absolute_url())
