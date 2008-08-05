import unittest

from zope.interface.verify import verifyObject
from zope.component import provideAdapter
from zope.component import getGlobalSiteManager
import zope.testing.cleanup

from Testing.ZopeTestCase import installProduct

# TextIndexNG3 mucks about with sys.path; we have to install it to be able
# to import from textindexng at all.
installProduct("TextIndexNG3", quiet=True)
try:
    from textindexng.interfaces.indexable import IIndexableContent
    from textindexng.interfaces.indexable import IIndexContentCollector
    from textindexng.interfaces.converter import IConverter
    from textindexng.converters.null import NullConverter
    TNG3 = True
except ImportError, e:
    TNG3 = False

from Products.Reflecto.content.file import ReflectoFile
from Products.Reflecto.content.directory import ReflectoDirectory
from Products.Reflecto.tests.utils import MockReflector

class IndexTests(unittest.TestCase):
    def setUp(self):
        self.reflector = MockReflector()


    def testTextualSearchableText(self):
        proxy=ReflectoFile(("reflecto.txt",)).__of__(self.reflector)
        self.failUnless("superhero" in proxy.SearchableText())
        self.failUnless("reflecto.txt" in proxy.SearchableText())


    def testBinarySearchableText(self):
        proxy=ReflectoFile(("reflecto.jpg",)).__of__(self.reflector)
        self.assertEqual(proxy.SearchableText(), "reflecto.jpg")

    def testDirectorySearchableText(self):
        proxy = ReflectoDirectory(('subdir',)).__of__(self.reflector)
        self.assertEqual(proxy.SearchableText(), 'subdir')


class FakeConvertor(object):
    pass


class TextIndexNG3Tests(unittest.TestCase):
    def setUp(self):
        from Products.Reflecto.catalog import \
            FileProxyIndexableContentAdapter
        self.reflector = MockReflector()
        getGlobalSiteManager().registerUtility(NullConverter, IConverter,
                'text/jpeg')

    def tearDown(self):
        zope.testing.cleanup.cleanUp()

    def testAdaption(self):
        proxy = ReflectoFile(("reflecto.jpg",)).__of__(self.reflector)
        indexer=IIndexableContent(proxy)
        self.failUnless(verifyObject(IIndexableContent, indexer))


    def testReturnTypeWithoutFields(self):
        proxy=ReflectoFile(("reflecto.jpg",)).__of__(self.reflector)
        indexer=IIndexableContent(proxy)
        self.assertEqual(indexer.indexableContent([]), None)


    def testReturnTypeWithFields(self):
        proxy=ReflectoFile(("reflecto.jpg",)).__of__(self.reflector)
        indexer=IIndexableContent(proxy)
        content=indexer.indexableContent(["Title"])
        self.failUnless(IIndexContentCollector.providedBy(content))
        self.failUnless(verifyObject(IIndexContentCollector, content))


    def testTitleIndex(self):
        proxy=ReflectoFile(("reflecto.jpg",)).__of__(self.reflector)
        indexer=IIndexableContent(proxy)
        content=indexer.indexableContent(["Title"])
        self.assertEqual(content.getFields(), ["Title"])
        self.assertEqual(content.getFieldData("Title")["content"],
                         "reflecto.jpg")


    def testBinaryContent(self):
        proxy=ReflectoFile(("reflecto.jpg",)).__of__(self.reflector)
        indexer=IIndexableContent(proxy)
        content=indexer.indexableContent(["SearchableText"])
        self.assertEqual(content.getFields(), ["SearchableText"])
        self.assertEqual(content.getFieldData("SearchableText")["mimetype"],
                proxy.Format())


    def testTextContent(self):
        proxy=ReflectoFile(("reflecto.txt",)).__of__(self.reflector)
        indexer=IIndexableContent(proxy)
        content=indexer.indexableContent(["SearchableText"])
        self.assertEqual(content.getFields(), ["SearchableText"])

        data=content.getFieldData("SearchableText")
        self.failUnless(isinstance(data["content"], unicode))
        self.failUnless(u"superhero" in data["content"])
        self.failUnless(u"reflecto.txt" in data["content"])



def test_suite():
    suite=unittest.TestSuite()
    suite.addTest(unittest.makeSuite(IndexTests))
    if TNG3:
        suite.addTest(unittest.makeSuite(TextIndexNG3Tests))
    return suite

