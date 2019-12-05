#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2019 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

from setuptools import setup


setup(name="release-tools",
      description="GrimoireLab release tools",
      author="Bitergia",
      author_email="sduenas@bitergia.com",
      license="GPLv3",
      packages=[
          'release_tools',
      ],
      install_requires=[
          'click>=0.7.0',
          'PyYAML>=5.1.2',
          'semver>=2.9.0',
      ],
      entry_points="""
          [console_scripts]
          changelog=release_tools.changelog:changelog
          semverup=release_tools.semverup:semverup
      """,
      zip_safe=False)
