from tempfile import TemporaryFile
from zipfile import ZipFile
from zope.publisher.browser import BrowserView
from Products.Reflecto.interfaces import IReflectoDirectory
from Products.Reflecto.interfaces import IReflectoFile
from Products.Reflecto.streaming import FileIterator
import os.path

class FileDownloadView(BrowserView):
    """Download ReflectoFiles as attachments (force save in browser)"""
    def __call__(self):
        self.request.response.setHeader(
            'Content-Disposition',
            'attachment; filename=%s' % self.context.getId())
        return self.context()


class DirectoryDownloadView(BrowserView):
    """Download Reflecto folders as zip files"""

    def acceptableName(self, name):
        """Test if a name is acceptable.

        We skip standard things like .svn and .git directories as well as the
        usual OSX Finder cruft.
        """
        return name not in frozenset([".svn", ".DS_Store", ".git"])


    def _addToZip(self, zip, entry, path=[]):
        newpath=path + [entry.__name__]

        if IReflectoDirectory.providedBy(entry):
            for key in entry.keys():
                if self.acceptableName(key):
                    self._addToZip(zip, entry[key], newpath)
        elif IReflectoFile.providedBy(entry):
            zip.write(entry.getFilesystemPath(), os.path.join(*newpath))


    def __call__(self):
        output=TemporaryFile()
        zip=ZipFile(output, "w")
        self._addToZip(zip, self.context)
        zip.close()

        output.seek(0, 0)
        iterator=FileIterator(output)

        self.request.response.setHeader(
            'Content-Disposition',
            'attachment; filename=%s.zip' % self.context.getId())
        self.request.response.setHeader("Content-Type", "application/zip")
        self.request.response.setHeader('Content-Length', len(iterator))

        return iterator


