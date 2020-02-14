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

import unittest

from release_tools.project import Project


class TestProject(unittest.TestCase):
    """Unit tests for Project"""

    @unittest.mock.patch('release_tools.project.GitHandler.root_path',
                         new_callable=unittest.mock.PropertyMock)
    def test_basepath(self, mock_root_path):
        """Check if the property returns the right path"""

        mock_root_path.return_value = "/tmp/repo/"

        project = Project('/tmp/repo/')

        expected = "/tmp/repo/"
        self.assertEqual(project.basepath, expected)

    @unittest.mock.patch('release_tools.project.GitHandler.root_path',
                         new_callable=unittest.mock.PropertyMock)
    def test_releases_path(self, mock_root_path):
        """Check if the property returns the releases path"""

        mock_root_path.return_value = "/tmp/repo/"

        project = Project('/tmp/repo/')

        expected = "/tmp/repo/releases"
        self.assertEqual(project.releases_path, expected)

    @unittest.mock.patch('release_tools.project.GitHandler.root_path',
                         new_callable=unittest.mock.PropertyMock)
    def test_unreleased_changes_path(self, mock_root_path):
        """Check if the property returns the path to the unreleased changes"""

        mock_root_path.return_value = "/tmp/repo/"

        project = Project('/tmp/repo/')

        expected = "/tmp/repo/releases/unreleased"
        self.assertEqual(project.unreleased_changes_path, expected)

    @unittest.mock.patch('release_tools.project.GitHandler.root_path',
                         new_callable=unittest.mock.PropertyMock)
    def test_pyproject_filepath(self, mock_root_path):
        """Check if the property returns the pyproject file path"""

        mock_root_path.return_value = "/tmp/repo/"

        project = Project('/tmp/repo/')

        expected = "/tmp/repo/pyproject.toml"
        self.assertEqual(project.pyproject_file, expected)

    @unittest.mock.patch('release_tools.project.GitHandler.find_file')
    @unittest.mock.patch('release_tools.project.GitHandler.root_path',
                         new_callable=unittest.mock.PropertyMock)
    def test_version_file(self, mock_root_path, mock_find_file):
        """Check if the property returns the version file path"""

        mock_root_path.return_value = "/tmp/repo/"
        mock_find_file.return_value = "/tmp/repo/_version.py"

        project = Project('/tmp/repo/')

        expected = "/tmp/repo/_version.py"
        self.assertEqual(project.version_file, expected)
        mock_find_file.assert_called_once_with('*_version.py')


if __name__ == '__main__':
    unittest.main()
