from Products.validation import validation
from Products.Reflecto.validators import isValidFilesystemPath
from Products.CMFCore.utils import ContentInit
from Products.CMFCore.DirectoryView import registerDirectory
from Products.Archetypes.public import process_types, listTypes
from Products.Reflecto.permissions import AddReflectorFolder
from Products.Reflecto.config import PROJECTNAME

registerDirectory("skins", globals())
validation.register(isValidFilesystemPath())

def initialize(context):
    import Products.Reflecto.content

    content_types, constructors, ftis = process_types(
        listTypes(PROJECTNAME), PROJECTNAME)

    ContentInit(
        PROJECTNAME + ' Content',
        content_types = content_types,
        permission = AddReflectorFolder,
        extra_constructors = constructors,
        fti = ftis,
        ).initialize(context)


