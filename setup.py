#!/usr/bin/env python

import distutils.core
from distutils.command.install import install
import os

class install_with_schemas(install):
  def run(self):
    install.run(self)

    os.system('gconftool-2 --install-schema-file elicit/data/elicit.schemas')

distutils.core.setup(
    name='elicit',
    version='2.0-pre1',
    description='Screen magnifier and color picker',
    author='Brian Mattern',
    author_email='rephorm@rephorm.com',
    url='http://www.rephorm.com/code/elicit',
    packages=['elicit'],
    package_data={'elicit': ['data/icons/*.png']},
    scripts=['bin/elicit'],
    data_files=[('/usr/share/gconf/schemas', ['elicit/data/elicit.schemas'])],
    cmdclass={'install': install_with_schemas}
    )

