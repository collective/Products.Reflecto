from zope.interface import implements

from AccessControl import ClassSecurityInfo

from Products.Archetypes.atapi import BaseContent
from Products.Archetypes.atapi import BaseSchema
from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import BooleanWidget
from Products.Archetypes.atapi import StringField
from Products.Archetypes.atapi import StringWidget
from Products.Archetypes.atapi import registerType

from Products.CMFCore.permissions import View
from Products.Reflecto.permissions import AddReflectorFolder
from Products.Reflecto.config import PROJECTNAME
from Products.Reflecto.interfaces import IReflector
from Products.Reflecto.interfaces import ILifeProxy
from Products.Reflecto.utils import makePathAbsolute
from Products.Reflecto.fields import InterfaceField

from Products.CMFDynamicViewFTI.browserdefault import BrowserDefaultMixin

from directory import ReflectoDirectoryBase

ReflectoSchema = BaseSchema + Schema((
    InterfaceField("life",
        write_permission = AddReflectorFolder,
        required = False,
        default = False,
        interface = ILifeProxy,
        widget = BooleanWidget(
            label = "Show life data",
            label_msgid = "life_label",
            description = "If this flag is set the life contents of the "
                          "filesystem will be shown. This makes Reflecto "
                          "a lot slower and prevents indexing of files.",
            description_msgid = "life_help",
            i18n_domain = "plone"),
        ),

    StringField("relativePath",
        write_permission = AddReflectorFolder,
        required = True,
        validators = ( "isValidFilesystemPath", ),
        widget = StringWidget(
            label = "Filesystem path",
            label_msgid = "reflex_path_label",
            description = "Please specify the directory which should be "
                          "exposed in your site. Either specify a path "
                          "relative to the Zope instance home or an "
                          "absolute path.",
            description_msgid = "reflex_path_help",
            i18n_domain = "plone")
        ),
    ))


class Reflector(ReflectoDirectoryBase, BaseContent, BrowserDefaultMixin):
    """Reflection of a filesystem folder."""

    __implements__ = (ReflectoDirectoryBase.__implements__,
                      BaseContent.__implements__,
                      BrowserDefaultMixin.__implements__)
    implements(IReflector)

    security = ClassSecurityInfo()
    schema = ReflectoSchema
    _at_rename_after_creation = True

    
    security.declareProtected(View, "getReflector")
    def getReflector(self):
        return self
    
    security.declareProtected(View, "getFilesystemPath")
    def getFilesystemPath(self):
        return makePathAbsolute(self.getRelativePath())

    security.declarePrivate('getPathToReflectoParent')
    def getPathToReflectoParent(self):
        return ()
    
    def __bobo_traverse__(self, REQUEST, name):
        try:
            return self[name]
        except KeyError:
            pass
        
        return BaseContent.__bobo_traverse__(self, REQUEST, name)

registerType(Reflector, PROJECTNAME)
