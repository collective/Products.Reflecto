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


    def acceptableEntry(self, entry):
        """Test if an entry is acceptable.

        This method performs more extensive tests on an object itself.
        Most noticably it checks if there is a list of path filters in
        the request parameters that should be honoured.
        """

        paths=self.request.form.get("paths", None)
        if not paths:
            return True

        entrypath=entry.getPhysicalPath()
        for path in paths:
            parts=tuple(path.split("/"))
            if entrypath[:len(parts)]==parts:
                return True

        return False


    def _addToZip(self, zip, entry, path=[]):
        newpath=path + [entry.__name__]

        if IReflectoDirectory.providedBy(entry):
            for key in entry.keys():
                if not self.acceptableName(key):
                    continue

                value=entry[key]
                if not self.acceptableEntry(value):
                    continue

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


