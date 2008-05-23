from zope.component import adapts
from zope.interface import implements
from zope.formlib.form import FormFields

from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.formlib.schema import SchemaAdapterBase
from Products.CMFPlone import PloneMessageFactory as _

from plone.app.controlpanel.form import ControlPanelForm

from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.Reflecto.interfaces import IReflectoConfigurationSchema

class ReflectoControlPanelAdapter(SchemaAdapterBase):

    adapts(IPloneSiteRoot)
    implements(IReflectoConfigurationSchema)

    def __init__(self, context):
        super(ReflectoControlPanelAdapter, self).__init__(context)
        pprop = getToolByName(context, 'portal_properties')
        self.context = pprop.site_properties

    def get_reflecto_hidden_files(self):
        return self.context.reflecto_hidden_files

    def set_reflecto_hidden_files(self, value):
        self.context._updateProperty('reflecto_hidden_files', value)

    reflecto_hidden_files = property(get_reflecto_hidden_files,
                                     set_reflecto_hidden_files)

class ReflectoControlPanel(ControlPanelForm):
    form_fields = FormFields(IReflectoConfigurationSchema)

    label = _(u"Reflecto configuration")
    description = _(u"Here you can configure site settings for Reflecto.")
    form_name = _(u"Hidden files")
