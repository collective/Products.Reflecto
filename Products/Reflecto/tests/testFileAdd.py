import os.path
import unittest

from tempfile import mkdtemp
from shutil import rmtree

from zope.formlib.form import Widgets


class MockContext(object):
    indexed = False
    
    # Pretend to be a reflecto directory
    def __init__(self, path):
        self.path = path
        
    def getFilesystemPath(self):
        return self.path
    
    def absolute_url(self):
        return 'reflecto/'
    
    def has_key(self, key):
        return key == 'existing'
    
    # Fake inner acquisition path 
    @property
    def aq_inner(self):
        return self
    
    # Pretend to be a returned reflecto object
    def __getitem__(self, key):
        if key == 'foo':
            return self
        raise KeyError(key)
    
    def indexObject(self):
        self.indexed = True
        
    # Pretend to be plone_utils
    @property
    def plone_utils(self):
        return self
    
    def addPortalMessage(self, message):
        self.portal_message = message


class MockFile(object):
    data = 'Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Ut amet.'
    
    def __init__(self, filename):
        self.filename = filename


class MockRequest(object):
    redirected = None
    
    # Pretend to be a response
    @property
    def response(self):
        return self
    
    def redirect(self, url):
        self.redirected = url


class FileAddViewTests(unittest.TestCase):
    def setUp(self):
        from Products.Reflecto.browser.addfile import FileAddForm
        self.path = mkdtemp()
        context = MockContext(self.path)
        self.view = FileAddForm(context, MockRequest())
        
    def tearDown(self):
        rmtree(self.path)
        
    def testGetFilePath(self):
        expected = os.path.join(self.path, 'foo')
        file = MockFile('foo')
        self.assertEqual(self.view.getFilePath(file), expected)
        
    def testAddValidateCorrect(self):
        data = dict(file=MockFile('foo'))
        # No widgets needed for this test
        self.view.widgets = Widgets((), prefix_length=0) 
        self.assertEqual(self.view.addValidate(None, data), [])
        
    def testAddValidateIncorrect(self):
        data = dict(file=MockFile('existing'))
        # No widgets needed for this test
        self.view.widgets = Widgets((), prefix_length=0) 
        errors = self.view.addValidate(None, data)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].field_name, 'file')
        
    def testAddValidateIE(self):
        # IE uses the full path for the filename, tsk tsk. Reflecto issue #7
        # No widgets needed for this test
        self.view.widgets = Widgets((), prefix_length=0) 
        data = dict(file=MockFile('C:\\monty\\foo'))
        self.assertEqual(self.view.addValidate(None, data), [])
        
        data = dict(file=MockFile('C:\\monty\\existing'))
        errors = self.view.addValidate(None, data)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].field_name, 'file')
        
    def testAddFile(self):
        data = dict(file=MockFile('foo'))
        # addFile has been wrapped into an action, reach inside
        self.view.addFile.success(data)
        
        newpath = os.path.join(self.path, 'foo')
        self.assertTrue(os.path.exists(newpath))
        self.assertEqual(open(newpath).read(), MockFile.data)
        
        self.assertEqual(self.view.request.redirected, 'reflecto/')
        
        self.assertTrue(self.view.context.portal_message is not None)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(FileAddViewTests))
    return suite

if __name__ == '__main__':
    unittest.main()
