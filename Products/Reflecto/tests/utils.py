from zope.interface import implements
from Products.Reflecto.interfaces import IReflector
import Acquisition
import os.path
import sys

samplesPath=os.path.join(sys.modules["Products.Reflecto.tests"].__path__[0],
                        "samples")


class MockReflector(Acquisition.Implicit):
    implements(IReflector)

    _at_uid = '35b46994-7454-4efa-8888-54c9b068230b'

    def getFilesystemPath(self):
        return samplesPath
