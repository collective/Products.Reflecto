"""Base class for unit tests.

Note that importing this module has various side-effects: it registers a set of
products with Zope, and it sets up a sandbox Plone site with the appropriate
products installed.
"""

import unittest
from Products.Archetypes.BaseObject import BaseObject

class ReflectoUnitTestCase(unittest.TestCase):
    """Base class for unit tests for the reflex' product.

    This may provide specific set-up and tear-down operations, or provide
    convenience methods.
    """
    def setUp(self):
        def Schema(self):
            return self.schema

        BaseObject.orig_schema=Schema
        BaseObject.Schema=Schema

    def tearDown(self):
        BaseObject.Schema=BaseObject.orig_schema
        del BaseObject.orig_schema




