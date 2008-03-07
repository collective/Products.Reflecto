from App.config import getConfiguration
from Products.Reflecto.validators import isValidFilesystemPath
import os, errno, sys
import unittest

class ValdidatorTests(unittest.TestCase):
    def setUp(self):
        self.home=getConfiguration().instancehome
        self.validator=isValidFilesystemPath()

    def testENOENT(self):
        def fakeStat(path):
            raise OSError(errno.ENOENT,
                            "No such file or directory: '%s'" % path)
        orig_stat=os.stat
        os.stat=fakeStat
        self.assertNotEqual(self.validator("/xxxxx"), 1)
        os.stat=orig_stat

    def testExistingFile(self):
        self.assertNotEqual(self.validator(sys.modules["os"].__file__), 1)

    def testExistingPath(self):
        self.assertEqual(self.validator(sys.modules["email"].__path__[0]), 1)


def test_suite():
    suite=unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ValdidatorTests))
    return suite

