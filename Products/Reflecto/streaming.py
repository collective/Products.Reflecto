import zope.interface
from ZPublisher.Iterators import IStreamIterator

class FileIterator(object):
    """ZPublisher iterator for existing already opened."""
    zope.interface.implements(IStreamIterator)

    def __init__(self, input, streamsize=1<<16):
        self.input=input
        self.streamsize=streamsize

    def next(self):
        data = self.input.read(self.streamsize)
        if not data:
            raise StopIteration
        return data

    def __len__(self):
        cur_pos = self.input.tell()
        self.input.seek(0, 2)
        size = self.input.tell()
        self.input.seek(cur_pos, 0)

        return size




