from Products.Reflecto.interfaces import IReflectoProxy
from Products.Reflecto.interfaces import IReflector
from hashlib import md5
from plone.uuid.interfaces import IUUID
from uuid import UUID
from zope.component import adapter
from zope.interface import implementer
import os.path


@implementer(IUUID)
@adapter(IReflectoProxy)
def reflectoUUID(context):
    # Short-circuit for top level.
    # We have to get the UID directly to avoid recursing
    if IReflector.providedBy(context):
        return getattr(context, '_at_uid', None)

    # Return a UUID based on the filesystem path
    path = os.path.join(*context.getPathToReflectoParent())
    reflector_uid = context.getReflector()._at_uid
    return str(UUID(bytes=md5(reflector_uid + path).digest()))
