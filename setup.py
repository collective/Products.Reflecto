from setuptools import setup, find_packages
import os

version = '2.5.1'

setup(name='Products.Reflecto',
      version=version,
      description="Access the filesystem from Plone",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Framework :: Plone",
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
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
