from zope.formlib import form
from zope.app.i18n import ZopeMessageFactory as _

from plone.app.controlpanel.form import ControlPanelForm

from Products.Reflecto.interfaces import IReflectoConfiguration

class ReflectoConfigurationForm(ControlPanelForm):
    form_fields = form.Fields(IReflectoConfiguration)

    label = _(u"Reflecto configuration")
    description = _(u"Here you can configure site settings for Reflecto.")
    form_name = _(u"Hidden files")
