#!/usr/bin/env python

import distutils.core
from distutils.command.install import install
import os

class install_with_schemas(install):
  def run(self):
    install.run(self)

    os.system('gconftool-2 --install-schema-file data/elicit.schemas')
    os.system('xdg-icon-resource install --size 16 data/icon/16/rephorm-elicit.png')
    os.system('xdg-icon-resource install --size 24 data/icon/24/rephorm-elicit.png')
    os.system('xdg-icon-resource install --size 32 data/icon/32/rephorm-elicit.png')
    os.system('xdg-desktop-menu install data/rephorm-elicit.desktop')

distutils.core.setup(
    name='elicit',
    version='2.0-pre2',
    description='Screen magnifier and color picker',
    author='Brian Mattern',
    author_email='rephorm@rephorm.com',
    url='http://www.rephorm.com/code/elicit',
    packages=['elicit'],
    package_data={'elicit': ['data/icons/*.png']},
    scripts=['bin/elicit'],
    data_files=[('/usr/share/gconf/schemas', ['data/elicit.schemas'])],
    cmdclass={'install': install_with_schemas}
    )

