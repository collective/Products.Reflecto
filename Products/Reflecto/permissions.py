from AccessControl import ModuleSecurityInfo
from Products.CMFCore.permissions import setDefaultRoles

security = ModuleSecurityInfo('Products.Reflecto.permissions')

security.declarePublic("AddReflector")
AddReflectorFolder="Add Reflector Folder"
setDefaultRoles(AddReflectorFolder, ("Manager",))

security.declarePublic("AddFilesystemObject")
AddFilesystemObject="Add Filesystem Object"
setDefaultRoles(AddFilesystemObject, ("Manager", "Owner"))
