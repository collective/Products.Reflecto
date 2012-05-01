import zope.interface

from Products.validation.interfaces.IValidator import IValidator
from Products.Reflecto.utils import makePathAbsolute
from Products.Reflecto.utils import cleanPath
from Products.Reflecto.utils import isDirectory

class isValidFilesystemPath(object):
    zope.interface.implements(IValidator)

    name = "isValidFilesystemPath"
    title = "Check if a filesystem path is valid"
    description = """Check if a filesystem path is syntactly correct and
                     refers to an existing directory."""

    def __init__(self, name=None):
        if name is not None:
            self.name=name

    def __call__(self, value, *args, **kwargs):
        path=makePathAbsolute(cleanPath(value))

        try:
            if not isDirectory(path):
                return "Not a directory"
        except OSError, e:
            return e.strerror

        return 1

