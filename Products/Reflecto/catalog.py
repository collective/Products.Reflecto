from zope.interface import implements
from zope.component import adapts
from Products.Reflecto.interfaces import IReflectoFile
from textindexng.interfaces.indexable import IIndexableContent
from textindexng.content import IndexContentCollector
from Products.Reflecto import chardet

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
        icc.addContent("Title", unicode(self.context.Title()))


    def indexSearchableText(self, icc):
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

