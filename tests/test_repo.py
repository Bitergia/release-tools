#!/usr/bin/env python3
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
#     Jose Javier Merchante <jjmerchante@bitergia.com>
#

import os
import shutil
import subprocess
import tempfile
import unittest


from release_tools.repo import (GitHandler,
                                RepositoryError)


REPOSITORY_ERROR = (
    r"fatal\: not a git repository \(or any of the parent directories\)\: \.git; code error\: 128"
)


class TestCaseRepo(unittest.TestCase):
    """Base class to test release-tools on a Git repo"""

    repo_name = 'sample-repo'
    submodule_name = 'sample-module'

    def setUp(self):
        self.tmp_path = tempfile.mkdtemp(prefix='release_tools_')
        self.git_path = os.path.join(self.tmp_path, self.repo_name)

        data_path = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(data_path, 'data')
        zip_path = os.path.join(data_path, self.repo_name + '.zip')

        subprocess.check_call(['unzip', '-qq', zip_path, '-d', self.tmp_path])

    def tearDown(self):
        shutil.rmtree(self.tmp_path)


class TestGitHandler(TestCaseRepo):
    """Unit tests for GitHandler"""

    def test_error(self):
        """Check if an exception is raised when there is an error calling Git commands."""

        with tempfile.TemporaryDirectory() as dirpath:
            with self.assertRaisesRegex(RepositoryError, REPOSITORY_ERROR):
                cmd = ['git', 'status']
                GitHandler._exec(cmd, cwd=dirpath, env={'LANG': 'C'})

    def test_root_path(self):
        repo = GitHandler(self.git_path)
        self.assertEqual(repo.root_path, self.git_path)

    def test_root_path_submodule(self):
        submodule_path = self.git_path + '/' + self.submodule_name
        repo = GitHandler(submodule_path)
        self.assertEqual(repo.root_path, submodule_path)

    def test_find_file(self):
        filename = 'README.md'
        repo = GitHandler(self.git_path)
        file_location = repo.find_file(filename)
        self.assertEqual(file_location, filename)

    def test_find_file_submodule(self):
        filename = 'a'
        submodule_path = self.git_path + '/' + self.submodule_name
        repo = GitHandler(submodule_path)
        file_location = repo.find_file(filename)
        self.assertEqual(file_location, filename)

    def test_find_file_missing(self):
        filename = 'a'
        repo = GitHandler(self.git_path)
        file_location = repo.find_file(filename)
        self.assertIsNone(file_location)


if __name__ == '__main__':
    unittest.main()
