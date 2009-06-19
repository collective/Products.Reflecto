from Products.Reflecto.content.reflector import Reflector
from Products.Reflecto.tests.utils import samplesPath
from Products.Reflecto.tests.zopecase import ReflectoZopeTestCase
from Testing.ZopeTestCase import ZopeTestCase
import unittest

class MockType:
    def __init__(self, result):
        self.result=result
    def normalized(self):
        return self.result

class MockMimeTypeRegistry:
    def __init__(self):
        self.extensions={}

    def lookupExtension(self, extension):
        result=self.extensions.get(extension, None)
        if result is not None:
            return MockType(result)


    def classify(self, data):
        return None


class DublinCoreTests(ReflectoZopeTestCase):
    # This needs to be a ZopeTestCase so we get an aq chain with an
    # application in it, which needed for the absolute_url call in
    # Identifier()
    def afterSetUp(self):
        ReflectoZopeTestCase.afterSetUp(self)
        self.folder.reflector=Reflector('reflector')
        self.reflector=self.folder.reflector
        self.reflector.setRelativePath(samplesPath)
        self.jpeg=self.reflector["reflecto.jpg"]
        self.text=self.reflector["reflecto.txt"]
        self.BIGJPEG=self.reflector["BIGFILE.JPG"]
        self.subdir=self.reflector["subdir"]


    def testTitle(self):
        self.assertEqual(self.jpeg.Title(), "reflecto.jpg")
        self.assertEqual(self.text.Title(), "reflecto.txt")
        self.assertEqual(self.subdir.Title(), "subdir")


    def testDescription(self):
        self.assertEqual(self.text.Description(), u"")
        self.assertEqual(self.subdir.Description(), u"")


    def testIdentifier(self):
        self.assertEqual(self.text.Identifier(),
                "http://nohost/test_folder_1_/reflector/reflecto.txt")
        self.assertEqual(self.subdir.Identifier(),
                "http://nohost/test_folder_1_/reflector/subdir")


    def testFormat(self):
        self.assertEqual(self.jpeg.Format(), "image/jpeg")
        self.assertEqual(self.text.Format(), "text/plain")
        self.assertEqual(self.subdir.Format(), "application/octet-stream")
        self.assertEqual(self.BIGJPEG.Format(), "image/jpeg")

    def testFormatWithMimeTypesRegistryForDirectory(self):
        self.folder.mimetypes_registry=MockMimeTypeRegistry()
        self.assertEqual(self.subdir.Format(), "application/octet-stream")

    def testFormatWithMimeTypesRegistryForFile(self):
        mtr = MockMimeTypeRegistry()
        mtr.extensions["jpg"]="audio/mp3"
        self.folder.mimetypes_registry=mtr
        self.assertEqual(self.jpeg.Format(), "audio/mp3")
        



def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

