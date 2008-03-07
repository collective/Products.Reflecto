from zope.publisher.browser import BrowserView

class FileDownloadView(BrowserView):
    """Download ReflectoFiles as attachments (force save in browser)"""
    def __call__(self):
        self.request.response.setHeader(
            'Content-Disposition',
            'attachment; filename=%s' % self.context.getId())
        return self.context()
