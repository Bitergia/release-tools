# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2020 Bitergia
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

import os

from release_tools.repo import GitHandler


PYPROJECT_FILENAME = 'pyproject.toml'
VERSION_FILENAME = '_version.py'

RELEASES_DIRNAME = 'releases'
UNRELEASED_CHANGES_DIRNAME = 'unreleased'


class Project:
    """Class to store a Python project structure."""

    def __init__(self, dirpath):
        self.repo = GitHandler(dirpath=dirpath)
        self._basepath = self.repo.root_path

    @property
    def basepath(self):
        """Base path of the project."""

        return self._basepath

    @property
    def pyproject_file(self):
        """Path to the project metadata file."""

        filepath = self.repo.find_file(PYPROJECT_FILENAME)
        return filepath

    @property
    def version_file(self):
        """Path to the project version file."""

        filepath = self.repo.find_file('*' + VERSION_FILENAME)
        return filepath

    @property
    def releases_path(self):
        """Path where release files are stored."""

        return os.path.join(self.basepath, RELEASES_DIRNAME)

    @property
    def unreleased_changes_path(self):
        """Path where the unreleased changes entries are stored."""

        return os.path.join(self.releases_path, UNRELEASED_CHANGES_DIRNAME)
