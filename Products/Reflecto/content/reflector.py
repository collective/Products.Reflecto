from zope.interface import implements

from AccessControl import ClassSecurityInfo

from Products.ATContentTypes.content.base import ATCTContent
from Products.ATContentTypes.content.schemata import ATContentTypeSchema

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
from Products.Reflecto.config import HAS_CACHESETUP

from webdav.Collection import Collection
from ZPublisher import xmlrpc
from Acquisition import aq_base

from directory import ReflectoDirectoryBase, ReflectoNullResource

ReflectoSchema = ATContentTypeSchema.copy() + Schema((
    InterfaceField("life",
        write_permission = AddReflectorFolder,
        required = False,
        default = False,
        interface = ILifeProxy,
        widget = BooleanWidget(
            label = "Show live data",
            label_msgid = "life_label",
            description = "If this flag is set the live contents of the "
                          "filesystem will be shown. This makes Reflecto "
                          "a lot slower and prevents indexing of files. "
                          "Please note that due to browser caching and "
                          "proxy servers users may still see cached older "
                          "data.",
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


if HAS_CACHESETUP:
    from Products.Archetypes.atapi import DisplayList
    from Products.Archetypes.atapi import SelectionWidget
    from Products.CMFCore.utils import getToolByName
    from Products.CacheSetup.config import CACHE_TOOL_ID

    ReflectoSchema += Schema((
        StringField("cacheRule",
            write_permission = AddReflectorFolder,
            default = "",
            required = False,
            vocabulary = "listReflectoCacheRules",
            widget = SelectionWidget(
                label       = "Cache rules",
                label_msgid = "reflex_cache_label",
                description = "This setting determines how files downloaded "
                              "from Reflecto will be cached. You can manage "
                              "the available cache rules through the cache "
                              "configuration tool in the Plone site setup. "
                              "This setting will only take effect if caching "
                              "is enabled in the cache configuration tool.",
                description_msgid = "reflex_cache_help",
                i18n_domain = "Plone"),
            ),
    ))

class Reflector(ReflectoDirectoryBase, Collection, ATCTContent):
    """Reflection of a filesystem folder."""

    implements(IReflector)

    security = ClassSecurityInfo()
    schema = ReflectoSchema
    _at_rename_after_creation = True

    
    security.declareProtected(View, "listReflectoCacheRules")
    def listReflectoCacheRules(self):
        if not HAS_CACHESETUP:
            return []

        pcs=getToolByName(self, CACHE_TOOL_ID, None)
        if pcs is None:
            return []
        rules=[(rule.getId(), rule.Title())
                for rule in pcs.getRules().objectValues("ContentCacheRule")
                    if "ReflectoFile" in rule.getContentTypes()]
        rules.sort(key=lambda x: x[1])

        vocab=DisplayList()
        vocab.add("", "Default browser caching")
        vocab+=DisplayList(rules)

        return vocab

    security.declareProtected(View, "getReflector")
    def getReflector(self):
        return self
    
    security.declareProtected(View, "getFilesystemPath")
    def getFilesystemPath(self):
        return makePathAbsolute(self.getRelativePath())

    security.declarePrivate("getPathToReflectoParent")
    def getPathToReflectoParent(self):
        return ()
    
    def __bobo_traverse__(self, REQUEST, name):
        try:
            return self[name]
        except KeyError:
            pass
        
        if hasattr(aq_base(self), name):
            return getattr(self, name)
        
        # webdav
        method = REQUEST.get('REQUEST_METHOD', 'GET').upper()
        if (method not in ('GET', 'POST') and not
              isinstance(REQUEST.RESPONSE, xmlrpc.Response) and
              REQUEST.maybe_webdav_client and not REQUEST.path):
            return ReflectoNullResource(self, name, REQUEST).__of__(self)
        
        return ATCTContent.__bobo_traverse__(self, REQUEST, name)


    def _referenceApply(self, methodName, *args, **kwargs):
        # We have no referenceable children, so pass.
        pass


registerType(Reflector, PROJECTNAME)
