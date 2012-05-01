import os.path

from zope import schema
from zope.interface import Interface
from zope.formlib import form
from zope.schema.interfaces import ValidationError

from zope.app.form.interfaces import WidgetInputError
try:
    from zope.app.i18n import ZopeMessageFactory as _
except ImportError:
    from zope.i18nmessageid import ZopeMessageFactory as _

from Products.CMFCore.utils import getToolByName
try:
    from Products.Five.formlib.formbase import FormBase
except ImportError:
    from five.formlib.formbase import FormBase


class IDirectoryAddForm(Interface):
    # XXX should we add a seperate id field? We can just use the
    # filename of the uploaded file, but what to do on filename
    # conflicts
    name = schema.ASCIILine(title=_(u"Directory name to add"),
                            required=True)


class DirectoryExistsError(ValidationError):
    __doc__ = _(u"The directory name is already in use.")


class DirectoryAddForm(FormBase):
    label = _(u"Add a new directory")

    form_fields = form.Fields(IDirectoryAddForm)

    def addValidate(self, action, data):
        errors = self.validate(action, data)
        if not errors:
            if self.context.has_key(data['name']):
                error = WidgetInputError("name", u"Dirertory name to add",
                                         DirectoryExistsError())
                errors.append(error)
        return errors

    @form.action(_("Add directory"), validator=addValidate)
    def addDirectory(self, action, data):
        name = data['name']
        path = os.path.join(self.context.getFilesystemPath(), name)
        os.mkdir(path, 0775)

        dir = self.context.aq_inner[name]
        dir.indexObject()

        pt=getToolByName(self.context, "plone_utils")
        pt.addPortalMessage(_(u'New directory created'))
        
        return self.request.response.redirect(
            self.context[name].absolute_url())
