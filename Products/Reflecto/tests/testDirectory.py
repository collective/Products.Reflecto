import operator
import os
import shutil
import stat
import tempfile
import unittest

from Acquisition import Implicit
from AccessControl import SecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from OFS.CopySupport import CopyError
from OFS.interfaces import IObjectWillBeRemovedEvent, IObjectWillBeMovedEvent
from OFS.interfaces import IObjectClonedEvent
from OFS.tests.testCopySupport import UnitTestSecurityPolicy, UnitTestUser

from zope.component.testing import PlacelessSetup as CASetup
from zope.component import provideAdapter
from zope.lifecycleevent.interfaces import (
    IObjectMovedEvent, IObjectRemovedEvent, IObjectCopiedEvent)
from zope.app.container.interfaces import IContainerModifiedEvent
from zope.component.eventtesting import PlacelessSetup as ESetup
from zope.component.eventtesting import getEvents
from zope.app.testing import ztapi
from Products.Reflecto.tests.unitcase import ReflectoUnitTestCase
from Products.Reflecto.interfaces import IReflectoDirectory

from zope.traversing.adapters import DefaultTraversable

from Products.Reflecto.interfaces import IReflectoFile
from Products.Reflecto.tests.utils import samplesPath

class DirectoryTests(ReflectoUnitTestCase):
    def setUp(self):
        from Products.Reflecto.content.reflector import Reflector
        super(DirectoryTests, self).setUp()
        self.reflecto = Reflector('reflecto')
        self.reflecto.setRelativePath(samplesPath)
        
    def testIndexOnNonExistingPath(self):
        # Raising OSError for ENOENT has many implications for the user
        # interface: it makes it impossible to import, paste or view
        # reflectors which have a non-existing path. This makes migrating
        # sites extremely hard.
        self.reflecto.setRelativePath("/this/does/not/exist")
        self.assertEqual(self.reflecto.keys(), [])

    def testNotExisting(self):
        self.assertRaises(KeyError, operator.itemgetter('nonesuch'),
                          self.reflecto)
        self.assertRaises(KeyError, operator.itemgetter(1),
                          self.reflecto)
    
    def testSimpleFile(self):
        self.assertTrue(IReflectoFile.providedBy(self.reflecto['reflecto.jpg']))
        
    def testDirectory(self):
        self.assertTrue(IReflectoDirectory.providedBy(self.reflecto['subdir']))
        
    def testDeepFile(self):
        self.assertTrue(IReflectoFile.providedBy(
            self.reflecto['subdir']['emptyfile.txt']))

    def testUnrestrictedTraverse(self):
        self.assertTrue(IReflectoFile.providedBy(
            self.reflecto.unrestrictedTraverse("reflecto.txt")))
        self.assertTrue(IReflectoDirectory.providedBy(
            self.reflecto.unrestrictedTraverse("subdir")))
        self.assertTrue(IReflectoFile.providedBy(
            self.reflecto.unrestrictedTraverse("subdir/emptyfile.txt")))
        
    def testIteration(self):
        names = set(self.reflecto)
        self.assertEqual(names, set(['reflecto.jpg', 'reflecto.png',
                                     'reflecto.txt', 'subdir', 'BIGFILE.JPG']))
    
    def testHasKey(self):
        self.assertTrue(self.reflecto.has_key('subdir'))
        self.assertFalse(self.reflecto.has_key('nonesuch'))
        
    def testAcceptableNames(self):
        self.assertFalse(self.reflecto.acceptableFilename("@@viewname"))
        self.assertTrue(self.reflecto.acceptableFilename("@viewname"))
        self.assertFalse(self.reflecto.acceptableFilename("++view++viewname"))
        self.assertFalse(self.reflecto.acceptableFilename(".."))
        self.assertFalse(self.reflecto.acceptableFilename("aq_parent"))
        # "Unicode" in fullwidth characters
        self.assertFalse(self.reflecto.acceptableFilename(
            u"\uff35\uff4e\uff49\uff43\uff4f\uff44\uff45"))
        
        
class MockIndexView:
    called = False
    def index(self):
        self.called = True
        
    def __of__(self, context):
        # Fake acquisition wrapping
        return self
    

class DirectoryFileManipulationBase(CASetup, ESetup, unittest.TestCase):
    def setUp(self):
        CASetup.setUp(self)
        ESetup.setUp(self)
        
        from Products.Reflecto.content.reflector import Reflector
        
        self.reflecto = Reflector('reflecto')
        self.indexview = MockIndexView()

        try:
            # Plone 3 needs a schema factory to be able to index things
            from Products.Archetypes.Schema.factory import instanceSchemaFactory
            provideAdapter(instanceSchemaFactory)
        except ImportError:
            pass
        
        # ease use of ITraversable by setting REQUEST to None
        self.reflecto.REQUEST = None
        # use the bog-standard traverser for views too
        provideAdapter(DefaultTraversable, (None,), name='view')
        # DefaultTraversable will look up the view as 'index'
        setattr(self.reflecto, 'index', self.indexview)
        
        self.tmppath = tempfile.mkdtemp()
        self.reflecto.setRelativePath(self.tmppath)
        
        os.mkdir(os.path.join(self.tmppath, 'subdir'))
        open(os.path.join(self.tmppath, 'foo'), 'w')
        open(os.path.join(self.tmppath, 'subdir', 'bar'), 'w')
        
    def tearDown(self):
        os.chmod(self.tmppath, stat.S_IRWXU)
        shutil.rmtree(self.tmppath)
        super(DirectoryFileManipulationBase, self).tearDown()
        
        
class DirectoryFileManipulationTests(DirectoryFileManipulationBase):
    def testDeleteNonExisting(self):
        self.assertRaises(KeyError, self.reflecto.manage_delObjects, ('monty',))
        self.assertRaises(KeyError, self.reflecto.manage_delObjects,
                          ('foo', 'monty',))
        self.assertTrue(os.path.exists(os.path.join(self.tmppath, 'foo')))
        
    def testDeleteNoAccess(self):
        os.chmod(self.tmppath, stat.S_IRUSR | stat.S_IXUSR) # read-only
        self.assertEqual(self.reflecto.manage_delObjects(('foo',)), ['foo'])
        self.assertTrue(os.path.exists(os.path.join(self.tmppath, 'foo')))
        
    def testDeleteFile(self):
        self.assertEqual(self.reflecto.manage_delObjects(('foo',)), None)
        self.assertTrue(self.indexview.called)
        self.assertFalse(os.path.exists(os.path.join(self.tmppath, 'foo')))
        
    def testDeleteDirectory(self):
        self.assertEqual(self.reflecto.manage_delObjects(('subdir',)), None)
        self.assertTrue(self.indexview.called)
        self.assertFalse(os.path.exists(os.path.join(self.tmppath, 'subdir')))
        
    def testDeleteEvents(self):
        self.assertRaises(KeyError, self.reflecto.manage_delObjects, ('monty',))
        self.assertEqual(len(getEvents()), 0)
        
        self.assertRaises(KeyError, self.reflecto.manage_delObjects,
                          ('foo', 'monty',))
        self.assertEqual(len(getEvents()), 1)
        events = getEvents(IObjectWillBeRemovedEvent)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].oldName, 'foo')
        
        self.assertEqual(self.reflecto.manage_delObjects(('foo',)), None)
        events = getEvents()
        self.assertEqual(len(events), 4)
        self.assertTrue(IObjectWillBeRemovedEvent.providedBy(events[1]))
        
        self.assertTrue(IObjectRemovedEvent.providedBy(events[2]))
        self.assertEqual(events[2].oldName, 'foo')
        
        self.assertTrue(IContainerModifiedEvent.providedBy(events[3]))
        self.assertTrue(events[3].object is self.reflecto)
        
    def testRenameNonExisting(self):
        self.assertRaises(KeyError, self.reflecto.manage_renameObjects, 
                          ('monty',), ('python',))
        self.assertRaises(KeyError, self.reflecto.manage_renameObjects,
                          ('foo', 'monty'), ('bar', 'python'))
        
    def testRenameNoAccess(self):
        os.chmod(self.tmppath, stat.S_IRUSR | stat.S_IXUSR) # read-only
        self.assertEqual(self.reflecto.manage_renameObjects(('foo',), ('bar',)),
                         [])
        self.assertTrue(os.path.exists(os.path.join(self.tmppath, 'foo')))
        self.assertFalse(os.path.exists(os.path.join(self.tmppath, 'bar')))
        
    def testRenameExisting(self):
        self.assertRaises(CopyError, self.reflecto.manage_renameObjects, 
                          ('foo',), ('subdir',))
        
    def testRenameFile(self):
        self.assertEqual(self.reflecto.manage_renameObjects(('foo',), ('bar',)),
                         ['foo'])
        self.assertTrue(self.indexview.called)
        self.assertFalse(os.path.exists(os.path.join(self.tmppath, 'foo')))
        self.assertTrue(os.path.isfile(os.path.join(self.tmppath, 'bar')))
        
    def testRenameDirectory(self):
        self.assertEqual(self.reflecto.manage_renameObjects(('subdir',), 
                                                            ('dirsub',)),
                         ['subdir'])
        self.assertTrue(self.indexview.called)
        self.assertFalse(os.path.exists(os.path.join(self.tmppath, 'subdir')))
        self.assertTrue(os.path.isdir(os.path.join(self.tmppath, 'dirsub')))
        
    def testRenameEvents(self):
        self.assertRaises(KeyError, self.reflecto.manage_renameObjects,
                          ('monty',), ('python',))
        self.assertEqual(len(getEvents()), 0)
        
        self.assertRaises(KeyError, self.reflecto.manage_renameObjects,
                          ('foo', 'monty'), ('bar', 'python'))
        self.assertEqual(len(getEvents()), 1)
        events = getEvents(IObjectWillBeMovedEvent)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].oldName, 'foo')
        self.assertEqual(events[0].newName, 'bar')
        
        self.assertEqual(self.reflecto.manage_renameObjects(('foo',), ('bar',)),
                         ['foo'])
        events = getEvents()
        self.assertEqual(len(events), 4)
        self.assertTrue(IObjectWillBeMovedEvent.providedBy(events[1]))
        
        self.assertTrue(IObjectMovedEvent.providedBy(events[2]))
        self.assertEqual(events[2].oldName, 'foo')
        self.assertEqual(events[2].newName, 'bar')
        
        self.assertTrue(IContainerModifiedEvent.providedBy(events[3]))
        self.assertTrue(events[3].object is self.reflecto)
        
        
class FakeRoot(Implicit):
    def getPhysicalRoot(self):
        return self
    
    def getPhysicalPath(self):
        return ('',)
    
    def unrestrictedTraverse(self, path):
        assert path[:2] == ('', 'reflecto')
        return self.reflecto.unrestrictedTraverse(path[2:])
    
    
class CopyPasteTests(DirectoryFileManipulationBase):
    def setUp(self):
        super(CopyPasteTests, self).setUp()
        
        from Products.Reflecto.content.reflector import Reflector
        
        self.root = FakeRoot()
        self.root.reflecto = self.reflecto
        self.reflecto = self.root.reflecto # Acquisition wrapped
        
        # Second reflector, using the subdir as it's filesystem path
        self.root.reflecto2 = Reflector('reflecto2')
        self.reflecto2 = self.root.reflecto2
        self.reflecto2.setRelativePath(os.path.join(self.tmppath, 'subdir'))
        self.indexview2 = MockIndexView()
        
        # duplicate fake @@index work for reflecto2
        if DefaultTraversable is not None:
            # ease use of ITraversable by setting REQUEST to None
            self.reflecto2.REQUEST = None
            # DefaultTraversable will look up the view as 'index'
            setattr(self.reflecto2, 'index', self.indexview2)
        else:
            setattr(self.reflecto2, '@@index', self.indexview2)
        
        self.oldpolicy = SecurityManager.setSecurityPolicy(
            UnitTestSecurityPolicy())
        newSecurityManager(None, UnitTestUser().__of__(self.root))
        
    def tearDown(self):
        noSecurityManager()
        SecurityManager.setSecurityPolicy(self.oldpolicy)
        
        del self.root
        del self.reflecto
        del self.oldpolicy
        
        super(CopyPasteTests, self).tearDown()
        
    def testCopyPasteNonexistent(self):
        self.assertRaises(AttributeError, self.reflecto.manage_copyObjects,
                          ('monty',))
        self.assertRaises(AttributeError, self.reflecto.manage_copyObjects,
                          ('monty', 'foo'))
        self.assertRaises(AttributeError, self.reflecto.manage_cutObjects,
                          ('monty',))
        self.assertRaises(AttributeError, self.reflecto.manage_cutObjects,
                          ('monty', 'foo'))
        
    def testCopyNoAccess(self):
        os.chmod(self.tmppath, stat.S_IRUSR | stat.S_IXUSR) # read-only
        cp = self.reflecto.manage_copyObjects(('foo',))
        self.assertEqual(self.reflecto.manage_pasteObjects(cp), [])
        self.assertFalse(os.path.isfile(
            os.path.join(self.tmppath, 'copy_of_foo')))
        
    def testCopyFile(self):
        cp = self.reflecto.manage_copyObjects(('foo',))
        self.assertEqual(self.reflecto.manage_pasteObjects(cp),
                         [dict(id='foo', new_id='copy_of_foo')])
        self.assertTrue(os.path.isfile(
            os.path.join(self.tmppath, 'copy_of_foo')))
        self.assertTrue(self.indexview.called)
        
    def testCopyDirectory(self):
        cp = self.reflecto.manage_copyObjects(('subdir',))
        self.assertEqual(self.reflecto.manage_pasteObjects(cp),
                         [dict(id='subdir', new_id='copy_of_subdir')])
        self.assertTrue(os.path.isdir(
            os.path.join(self.tmppath, 'copy_of_subdir')))
        self.assertTrue(os.path.isfile(
            os.path.join(self.tmppath, 'copy_of_subdir', 'bar')))
        self.assertTrue(self.indexview.called)
        
    def testCopyAcross(self):
        cp = self.reflecto.manage_copyObjects(('foo',))
        self.assertEqual(self.reflecto2.manage_pasteObjects(cp),
                         [dict(id='foo', new_id='foo')])
        self.assertTrue(os.path.isfile(
            os.path.join(self.tmppath, 'subdir', 'foo')))
        self.assertTrue(self.indexview2.called)
        
    def testCopyEvents(self):
        cp = self.reflecto.manage_copyObjects(('foo',))
        self.reflecto.manage_pasteObjects(cp)
        
        events = getEvents()
        self.assertEqual(len(events), 3)
        
        self.assertTrue(IObjectCopiedEvent.providedBy(events[0]))
        self.assertEqual(events[0].original.getId(), 'foo')
        self.assertEqual(events[0].object.getId(), 'copy_of_foo')
        
        self.assertTrue(IObjectClonedEvent.providedBy(events[1]))
        self.assertEqual(events[1].object.getId(), 'copy_of_foo')
        
        self.assertTrue(IContainerModifiedEvent.providedBy(events[2]))
        self.assertTrue(events[2].object is self.reflecto)
        
    def testCutNoAccess(self):
        os.chmod(self.tmppath, stat.S_IRUSR | stat.S_IXUSR) # read-only
        cp = self.reflecto.manage_cutObjects(('foo',))
        self.assertEqual(self.reflecto['subdir'].manage_pasteObjects(cp), [])
        self.assertFalse(os.path.isfile(
            os.path.join(self.tmppath, 'subdir', 'foo')))
        
    def testCutFile(self):
        cp = self.reflecto.manage_cutObjects(('foo',))
        self.assertEqual(self.reflecto['subdir'].manage_pasteObjects(cp),
                         [dict(id='foo', new_id='foo')])
        self.assertFalse(os.path.isfile(
            os.path.join(self.tmppath, 'foo')))
        self.assertTrue(os.path.isfile(
            os.path.join(self.tmppath, 'subdir', 'foo')))
        self.assertTrue(self.indexview.called)
        
    def testCutDirectory(self):
        os.mkdir(os.path.join(self.tmppath, 'otherdir'))
        
        cp = self.reflecto.manage_cutObjects(('subdir',))
        self.assertEqual(self.reflecto['otherdir'].manage_pasteObjects(cp),
                         [dict(id='subdir', new_id='subdir')])
        self.assertFalse(os.path.isdir(
            os.path.join(self.tmppath, 'subdir')))
        self.assertTrue(os.path.isdir(
            os.path.join(self.tmppath, 'otherdir', 'subdir')))
        self.assertTrue(os.path.isfile(
            os.path.join(self.tmppath, 'otherdir', 'subdir', 'bar')))
        self.assertTrue(self.indexview.called)
        
    def testCutAcross(self):
        cp = self.reflecto.manage_cutObjects(('foo',))
        self.assertEqual(self.reflecto2.manage_pasteObjects(cp),
                         [dict(id='foo', new_id='foo')])
        self.assertFalse(os.path.isfile(
            os.path.join(self.tmppath, 'foo')))
        self.assertTrue(os.path.isfile(
            os.path.join(self.tmppath, 'subdir', 'foo')))
        self.assertTrue(self.indexview.called)
        self.assertTrue(self.indexview2.called)

    def testCutPasteIntoSelf(self):
        cp = self.reflecto.manage_cutObjects(('subdir',))
        self.assertRaises(CopyError,
                          self.reflecto['subdir'].manage_pasteObjects, cp)
        
    def testCutEvents(self):
        cp = self.reflecto.manage_cutObjects(('foo',))
        self.reflecto['subdir'].manage_pasteObjects(cp)
        
        events = getEvents()
        self.assertEqual(len(events), 4)
        
        self.assertTrue(IObjectWillBeMovedEvent.providedBy(events[0]))
        self.assertEqual(events[0].oldName, 'foo')
        self.assertEqual(events[0].oldParent, self.reflecto)
        self.assertEqual(events[0].newName, 'foo')
        self.assertEqual(events[0].newParent, self.reflecto['subdir'])
        
        self.assertTrue(IObjectMovedEvent.providedBy(events[1]))
        self.assertEqual(events[1].object.getId(), 'foo')
        
        self.assertTrue(IContainerModifiedEvent.providedBy(events[2]))
        self.assertEqual(events[2].object, self.reflecto)
        self.assertTrue(IContainerModifiedEvent.providedBy(events[3]))
        self.assertEqual(events[3].object, self.reflecto['subdir'])

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DirectoryTests))
    suite.addTest(unittest.makeSuite(DirectoryFileManipulationTests))
    suite.addTest(unittest.makeSuite(CopyPasteTests))
    return suite
