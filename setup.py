#!/usr/bin/env python

from setuptools import setup
from setuptools import find_packages

setup(name='blogit',
      version='0.1',
      license="GNU GPL",
      packages=find_packages(exclude=['tests']),
      install_requires=['Jinja2', 'markdown2', 'tinydb', 'pygments'],
      tests_require=['pytest', 'beautifulsoup4'],
      entry_points={
              'console_scripts': ['blogit = blogit.blogit:main']
          },

      classifiers=['Environment :: Console',
                   'Intended Audience :: End Users/Desktop',
                   'Intended Audience :: Developers',
                   ('License :: OSI Approved :: GNU General Public License'
                    ' v3 or later (GPLv3+)'),
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   ],
      )

