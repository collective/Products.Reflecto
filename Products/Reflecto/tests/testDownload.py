from ZPublisher.Iterators import IStreamIterator
from Products.Reflecto.content.reflector import Reflector
from Products.Reflecto.tests.utils import samplesPath
from Products.Reflecto.tests.zopecase import ReflectoZopeTestCase
from Products.Reflecto.browser.download import DirectoryDownloadView
from Testing.ZopeTestCase import ZopeTestCase
import unittest

class DirectoryDownloadTests(ReflectoZopeTestCase):
    def afterSetUp(self):
        super(DirectoryDownloadTests, self).afterSetUp()
        self.folder.reflector=Reflector('reflector')
        self.reflector=self.folder.reflector
        self.reflector.setRelativePath(samplesPath)
        self.subdir=self.reflector["subdir"]
        self.view=DirectoryDownloadView(self.reflector, self.app.REQUEST)

    def testIgnoreOSXMadness(self):
        self.assertEqual(self.view.acceptableName(".DS_Store"), False)

    def testIgnoreVersionControlData(self):
        self.assertEqual(self.view.acceptableName(".git"), False)
        self.assertEqual(self.view.acceptableName(".svn"), False)

    def testAcceptEntriesWithoutPathFilter(self):
        entry=self.reflector["subdir"]
        self.assertEqual(self.view.acceptableEntry(entry), True)

    def testAcceptEntriesWithEmptyPathFilter(self):
        self.app.REQUEST.form["paths"]=()
        entry=self.reflector["subdir"]
        self.assertEqual(self.view.acceptableEntry(entry), True)

    def testRefuseEntryOutsideRequestPath(self):
        self.app.REQUEST.form["paths"]=("/test_folder_1_/reflector/other",)
        entry=self.reflector["subdir"]
        self.assertEqual(self.view.acceptableEntry(entry), False)

    def testAcceptEntryInPathFilter(self):
        self.app.REQUEST.form["paths"]=("/test_folder_1_/reflector",)
        entry=self.reflector["subdir"]
        self.assertEqual(self.view.acceptableEntry(entry), True)

    def testAcceptSubEntryInPathFilter(self):
        self.app.REQUEST.form["paths"]=("/test_folder_1_/reflector",)
        entry=self.reflector["subdir"]["emptyfile.txt"]
        self.assertEqual(self.view.acceptableEntry(entry), True)

    def testDownloadReturnsIterator(self):
        result=self.view()
        self.failUnless(IStreamIterator.isImplementedBy(result))

    def testIteratorDataAtStartOfFile(self):
        # Originally I forgot to seek to the start of the file...
        result=self.view()
        self.assertEqual(result.input.tell(), 0L)

    def testContentLengthHeader(self):
        result=self.view()
        response=self.app.REQUEST.response
        self.assertEqual(response.getHeader("Content-Length"), str(len(result)))



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DirectoryDownloadTests))
    return suite

