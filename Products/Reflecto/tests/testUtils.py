from App.config import getConfiguration
from Products.Reflecto.utils import makePathAbsolute
from Products.Reflecto.utils import cleanPath
import os.path
import unittest

class PathTests(unittest.TestCase):
    def setUp(self):
        self.home=getConfiguration().instancehome

    def testPathNormalization(self):
        self.assertEqual(cleanPath("/tmp/"), "/tmp")
        self.assertEqual(cleanPath("/tmp//"), "/tmp")
        self.assertEqual(cleanPath("/tmp/../tmp/"), "/tmp")

    def testPathRelativising(self):
        self.assertEqual(cleanPath(self.home), "")
        self.assertEqual(cleanPath(os.path.join(self.home, "import")), "import")

    def testAbsolution(self):
        self.assertEqual(makePathAbsolute(""), self.home)
        self.assertEqual(makePathAbsolute("/tmp"), "/tmp")



def test_suite():
    suite=unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PathTests))
    return suite
