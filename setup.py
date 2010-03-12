#!/usr/bin/env python

from distutils.core import setup

setup(name='Elicit',
      version='2.0',
      description='Screen magnifier and color picker',
      author='Brian Mattern',
      author_email='rephorm@rephorm.com',
      url='http://www.rephorm.com/code/elicit',
      packages=['elicit'],
      package_data={'elicit': ['data/icons/*.png']},
      scripts=['bin/elicit'],
      data_files=[('/usr/share/gconf/schemas', ['elicit/data/elicit.schemas'])]
      )

