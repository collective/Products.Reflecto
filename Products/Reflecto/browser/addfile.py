from zope.interface import Interface
from zope import schema
try:
    from zope.app.i18n import ZopeMessageFactory as _
except ImportError:
    from zope.i18nmessageid import ZopeMessageFactory as _
from Products.CMFCore.utils import getToolByName
from Products.Reflecto.formlib.interfaces import INamedFile
from Products.Reflecto.formlib.file import NamedFileWidget
from zope.formlib import form
try:
    from Products.Five.formlib.formbase import FormBase
except ImportError:
    from five.formlib.formbase import FormBase
from zope.app.form.interfaces import WidgetInputError
from zope.schema.interfaces import ValidationError
import os
import os.path


class IFileAddForm(Interface):
    # XXX should we add a seperate id field? We can just use the
    # filename of the uploaded file, but what to do on filename
    # conflicts
    file = schema.Object(schema=INamedFile,
                        title=_(u"File to add"),
                        required=True)


class FileExistsError(ValidationError):
    __doc__ = _(u"A file with the same filename already exists.")


class FileAddForm(FormBase):
    label = _(u"Add a new file")

    form_fields = form.Fields(IFileAddForm).select("file")
    form_fields["file"].custom_widget = NamedFileWidget

    def getFilePath(self, file):
        return os.path.join(self.context.getFilesystemPath(), file.filename)


    def addValidate(self, action, data):
        errors = self.validate(action, data)
        if not errors:
            # IE includes the full path (security violation!). Strip it off.
            data['file'].filename = data['file'].filename.split('\\')[-1]
            if self.context.has_key(data['file'].filename):
                error=WidgetInputError("file", u"File to add",
                                        FileExistsError())
                errors.append(error)
        return errors


    @form.action(_("Add file"), validator=addValidate)
    def addFile(self, action, data):
        file=data["file"]
        path=self.getFilePath(file)
        # We care about security so use O_CREAT|O_EXCL to prevent us
        # from hitting symlinks or other race attacks.
        try:
            # For OSes which support it (Windows) we need to use the
            # O_BINARY flag to prevent cr/lf rewriting.
            flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_BINARY
        except AttributeError:
            flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL
        fd=os.open(path, flags, 0644)
        os.write(fd, file.data)
        os.close(fd)

        reflex = self.context.aq_inner[file.filename]
        reflex.indexObject()

        pt=getToolByName(self.context, "plone_utils")
        pt.addPortalMessage(_(u"File uploaded and indexed"))
        return self.request.response.redirect(self.context.absolute_url())

