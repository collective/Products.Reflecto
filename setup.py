from setuptools import setup, find_packages
import os

version = '3.0.7dev'

setup(name='Products.Reflecto',
      version=version,
      description="Access the filesystem from Plone",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
          "Framework :: Plone :: 3.3",
          "Framework :: Plone :: 4.0",
          "Framework :: Plone :: 4.1",
          "Framework :: Plone :: 4.2",
          "Framework :: Plone :: 4.3",
          "Framework :: Plone :: 5.0",
          "Framework :: Plone :: 5.1",
          "Programming Language :: Python",
          "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='plone filesystem',
      author='Jarn AS',
      author_email='support@jarn.com',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'zope.app.file',
          'zope.app.form<=4.0.2',
          'zope.formlib<=4.2.1',
          'five.formlib<=1.0.4',
          'Products.ATContentTypes',
      ]
      )
