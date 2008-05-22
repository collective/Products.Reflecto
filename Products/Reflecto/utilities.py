from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty

from interfaces import IReflectoConfiguration

from OFS.SimpleItem import SimpleItem

class ReflectoConfiguration(SimpleItem):
    implements(IReflectoConfiguration)
    
    hidden_files = FieldProperty(IReflectoConfiguration['hidden_files'])
