from AccessControl import ClassSecurityInfo
from Products.Archetypes.atapi import BooleanField
from Products.Reflecto.utils import addMarkerInterface
from Products.Reflecto.utils import removeMarkerInterface


class InterfaceField(BooleanField):
    _properties = BooleanField._properties.copy()
    _properties.update({
        "interface" : None,
        })

    security  = ClassSecurityInfo()


    security.declarePrivate("getInterfaces")
    def getInterfaces(self):
        if isinstance(self.interface, tuple):
            return self.interface
        else:
            return (self.interface,)


    security.declarePrivate("set")
    def set(self, instance, value, **kwargs):
        if not value or value == "0" or value == "False":
            value = False
        else:
            value = True

        if value:
            addMarkerInterface(instance, *self.getInterfaces())
        else:
            removeMarkerInterface(instance, *self.getInterfaces())


    security.declarePrivate("get")
    def get(self, instance, **kwargs):
        for iface in self.getInterfaces():
            if not iface.providedBy(instance):
                return False
        return True

    security.declarePrivate("getRaw")
    getRaw = get



