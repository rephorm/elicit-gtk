#!/usr/bin/env python

import distutils.core
from distutils.command.install import install
import os
import elicit.appinfo as appinfo

class install_with_schemas(install):
  def run(self):
    install.run(self)

    os.system('gconftool-2 --install-schema-file data/elicit.schemas')
    os.system('xdg-icon-resource install --size 16 data/icon/16/rephorm-elicit.png')
    os.system('xdg-icon-resource install --size 24 data/icon/24/rephorm-elicit.png')
    os.system('xdg-icon-resource install --size 32 data/icon/32/rephorm-elicit.png')
    os.system('xdg-icon-resource install --size 48 data/icon/48/rephorm-elicit.png')
    os.system('xdg-desktop-menu install data/rephorm-elicit.desktop')

distutils.core.setup(
    name=appinfo.pkgname,
    version=appinfo.version,
    description=appinfo.description,
    author=appinfo.author,
    author_email=appinfo.author_email,
    url=appinfo.website,
    packages=[appinfo.pkgname],
    package_data={appinfo.pkgname: ['data/icons/*.png']},
    scripts=['bin/elicit', 'bin/elicit_remote'],
    data_files=[
      ('/usr/share/gconf/schemas', ['data/elicit.schemas']),
      ('/usr/share/dbus-1/services', ['data/com.rephorm.elicit.service'])
      ],
    cmdclass={'install': install_with_schemas}
    )

