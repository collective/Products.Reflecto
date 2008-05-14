import os.path
import stat
from App.config import getConfiguration
from zope.interface import alsoProvides
from zope.interface import noLongerProvides


def makePathAbsolute(path):
    """Turn a path relative to INSTANCE_HOME into an absolute path."""
    path=os.path.join(getConfiguration().instancehome, path)
    return os.path.normpath(path)


def cleanPath(path):
    """Cleanup a path to produce a normalized filesystem path.

    If possible a path is made relative to the INSTANCE_HOME
    """

    path=os.path.normpath(path)
    if os.path.isabs(path):
        home=os.path.normpath(getConfiguration().instancehome)

        if path==home or path.startswith(home+os.path.sep):
            path=path[len(home)+1:]

    return path


def isDirectory(path):
    """Test if an absolute path refers to a directory.

    Unlike the os.path.isdir method this method will raise an exception if
    the file does not exist. This allows us to use a single stat(2) call
    to test both existance and directorishness.
    """
    mode=os.stat(path)[stat.ST_MODE]
    return stat.S_ISDIR(mode)


def addMarkerInterface(obj, *ifaces):
    for iface in ifaces:
        if not iface.providedBy(obj):
            alsoProvides(obj, iface)


def removeMarkerInterface(obj, *ifaces):
    for iface in ifaces:
        if iface.providedBy(obj):
            noLongerProvides(obj, iface)


