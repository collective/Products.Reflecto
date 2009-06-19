import unittest
from zope.interface.verify import verifyObject
from Products.Reflecto.tests.unitcase import ReflectoUnitTestCase
from Products.Reflecto.tests.utils import samplesPath
from Products.Reflecto.content.reflector import Reflector
from Products.Reflecto.interfaces import IIndexView
from Products.Reflecto.browser.index import IndexView
from zope.publisher.browser import TestRequest


class MockBrain:
    def __init__(self, path):
        self.path=path

    def getPath(self):
        return self.path


class MockCatalog:
    def __init__(self):
        self.searches=[]
        self.indexed=[]
        self.removed=[]
        self.results=[]

    def indexObject(self, object):
        self.indexed.append(object)

    def searchResults(self, query):
        self.searches.append(query)
        return self.results

    def uncatalog_object(self, path):
        self.removed.append(path)



class IndexTests(ReflectoUnitTestCase):
    def setUp(self):
        super(IndexTests, self).setUp()
        self.reflector=Reflector('reflector')
        self.reflector.setRelativePath(samplesPath)

    def testTextFileIndex(self):
        file=self.reflector["reflecto.txt"]
        file.portal_catalog=MockCatalog()
        file.indexObject()
        self.assertEqual(file.portal_catalog.indexed, [file])

    def testDirectoryIndex(self):
        dir=self.reflector["subdir"]
        dir.portal_catalog=MockCatalog()
        dir.indexObject()
        self.assertEqual(dir.portal_catalog.indexed, [dir])



class IndexViewTests(unittest.TestCase):
    def setUp(self):
        self.reflector=Reflector('reflector')
        self.reflector.setRelativePath(samplesPath)
        self.reflector.portal_catalog=MockCatalog()

    def createView(self, context=None):
        if context is None:
            context=self.reflector
        view=IndexView(context, TestRequest())
        return view


    def testViewBasics(self):
        view=self.createView()
        self.failUnless(IIndexView.providedBy(view))
        self.failUnless(verifyObject(IIndexView, view))


    def testFileIndex(self):
        file=self.reflector["reflecto.txt"]
        view=self.createView(file)
        view.index()
        results=["/".join(x.getPathToReflectoParent()) \
                    for x in self.reflector.portal_catalog.indexed]
        self.assertEqual(results, ["reflecto.txt"])


    def testSubdirIndex(self):
        dir=self.reflector["subdir"]
        view=self.createView(dir)
        view.index()
        results=["/".join(x.getPathToReflectoParent()) \
                    for x in self.reflector.portal_catalog.indexed]
        self.assertEqual(set(results), set(["subdir", "subdir/emptyfile.txt"]))


    def testNoSubdirIndexInLifeMode(self):
        self.reflector.setLife(True)
        dir=self.reflector["subdir"]
        view=self.createView(dir)
        view.index()
        self.assertEqual(self.reflector.portal_catalog.indexed, [])


    def testFileUnindex(self):
        file=self.reflector["reflecto.txt"]
        view=self.createView(file)
        self.reflector.portal_catalog.results=[MockBrain("reflecto.txt")]
        view.unindex()
        self.assertEqual(self.reflector.portal_catalog.indexed, [])
        self.assertEqual(self.reflector.portal_catalog.searches,
                [{'path': 'reflector/reflecto.txt'}])
        self.assertEqual(self.reflector.portal_catalog.removed,
                ["reflecto.txt"])


    def testDirectoryUnindex(self):
        dir=self.reflector["subdir"]
        view=self.createView(dir)
        self.reflector.portal_catalog.results=[MockBrain("subdir"),
                                               MockBrain("subdir/reflecto.txt")]
        view.unindex()
        self.assertEqual(self.reflector.portal_catalog.indexed, [])
        self.assertEqual(self.reflector.portal_catalog.searches,
                [{"path": "reflector/subdir"}])
        self.assertEqual(set(self.reflector.portal_catalog.removed),
                set(["subdir", "subdir/reflecto.txt"]))



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(IndexTests))
    suite.addTest(unittest.makeSuite(IndexViewTests))
    return suite

