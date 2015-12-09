#!/usr/bin/env python

from setuptools import setup
from setuptools import find_packages

setup(name='blogit',
      version='0.0.1',
      license="GNU GPL",
      packages=find_packages(exclude=['tests']),
      entry_points={
              'console_scripts': ['blogit = blogit.blogit:main']
          }
      )

