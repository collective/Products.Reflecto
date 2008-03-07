from zope.interface import implements
from Products.Reflecto.interfaces import IReflector
import Acquisition
import os.path
import sys

samplesPath=os.path.join(sys.modules["Products.Reflecto.tests"].__path__[0],
                        "samples")


class MockReflector(Acquisition.Implicit):
    implements(IReflector)

    def getFilesystemPath(self):
        return samplesPath

