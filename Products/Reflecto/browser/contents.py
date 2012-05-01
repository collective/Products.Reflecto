from Products.Five.browser import BrowserView
try:
    from Products.CMFPlone import Batch
except ImportError:
    from Products.CMFPlone.PloneBatch import Batch

class LifeContents(BrowserView):

    def __call__(self):
        """getFolderContents alternative for life reflectors.
        This should return brain-like objects.
        """

        return Batch(self.context.values(), 100, int(self.request.get("b_start", 0)), orphan=0)



