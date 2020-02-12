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
#

import tempfile
import unittest


from release_tools.repo import (GitHandler,
                                RepositoryError)


REPOSITORY_ERROR = (
    r"fatal\: not a git repository \(or any of the parent directories\)\: \.git; code error\: 128"
)


class TestGitHandler(unittest.TestCase):
    """Unit tests for GitHandler"""

    def test_error(self):
        """Check if an exception is raised when there is an error calling Git commands."""

        with tempfile.TemporaryDirectory() as dirpath:
            with self.assertRaisesRegex(RepositoryError, REPOSITORY_ERROR):
                cmd = ['git', 'status']
                GitHandler._exec(cmd, cwd=dirpath, env={'LANG': 'C'})


if __name__ == '__main__':
    unittest.main()
