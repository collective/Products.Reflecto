import unittest
from Products.Reflecto.tests.utils import MockReflector


class UUIDTests(unittest.TestCase):

    def setUp(self):
        self.reflector = MockReflector()

    def testReflectorUUID(self):
        from Products.Reflecto.uuids import reflectoUUID
        uid = reflectoUUID(self.reflector)
        self.assertEqual(uid, self.reflector._at_uid)

    def testProxyUUID(self):
        from Products.Reflecto.uuids import reflectoUUID
        from Products.Reflecto.content.file import ReflectoFile
        proxy = ReflectoFile(("reflecto.txt",)).__of__(self.reflector)
        uid = reflectoUUID(proxy)
        self.assertFalse(uid == self.reflector._at_uid)
