from zope.interface import Interface
from zope.app.container.interfaces import IReadContainer

class IReflector(Interface):
    """Reflection of a filesystem folder."""



class IReflectoProxy(Interface):
    """A reflecto proxied filesystem object."""

    def getReflector():
        """Return our Reflector object.
        """


    def getPathToReflectoParent():
        """Return a path from the reflex object to this proxy.

        The path will be a tuple of strings.
        """


    def getFilesystemPath():
        """Return the absolute filesystem path for this object.
        """
        


class IReflectoDirectory(IReflectoProxy, IReadContainer):
    """A reflexion of a directory"""
    


class IReflectoFile(IReflectoProxy):
    """A reflection of a file"""

    
    def getFileContent():
        """Is it really Superboy?

        Data has to be returned as a raw string.
        """


class ILifeProxy(Interface):
    """A marker interface for reflectors which should show life filesystem
    data instead of catalogued files."""


class IIndexView(Interface):
    def unindex():
        """Remove a reflector proxy from the catalog.

        If the object is of a directory type all its children will also
        be removed from the catalog.
        """


    def index():
        """(Re)index a reflex proxy and its children.

        This will completely reindex and update a reflex proxy object
        with the filesystem data. Any newly created entries on the filesystem
        will be added and removed entries will be deleted from the catalog.
        """

