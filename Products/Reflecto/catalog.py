from zope.interface import implements
from zope.component import adapts
from Products.Reflecto.interfaces import IReflectoFile
try:
    from zopyx.txng3.core.interfaces import IIndexableContent
    from zopyx.txng3.core.content import IndexContentCollector
except ImportError:
    from textindexng.interfaces.indexable import IIndexableContent
    from textindexng.content import IndexContentCollector

from Products.Reflecto import chardet

from Products.CMFPlone.utils import safe_unicode

class FileProxyIndexableContentAdapter(object):
    implements(IIndexableContent)
    adapts(IReflectoFile)

    def __init__(self, context):
        self.context=context


    @property
    def hasTextContent(self):
        (major,minor)=self.context.Format().split("/", 1)
        return major in [ "message", "text" ]


    def indexTitle(self, icc):
        icc.addContent("Title", safe_unicode(self.context.Title()))


    def indexSearchableText(self, icc):
        icc.addContent("SearchableText", safe_unicode(self.context.Title()))
        data=self.context.getFileContent()
        if self.hasTextContent:
            encoding=chardet.detect(data)["encoding"]
            icc.addContent("SearchableText",
                    data.decode(encoding, "ignore"))
        else:
            icc.addBinary("SearchableText", data, self.context.Format())


    def indexableContent(self, fields):
        icc=IndexContentCollector()

        for field in fields:
            method="index"+field
            if hasattr(self, method):
                getattr(self, method)(icc)

        if not icc.getFields():
            return None

        return icc

