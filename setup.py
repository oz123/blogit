#!/usr/bin/env python

from setuptools import setup
from setuptools import find_packages

setup(name='blogit2',
      version='0.0.1',
      license="GNU GPL",
      entry_points={
          'console_scripts': ['blogit2 = blogit2:main']
          }
      )

