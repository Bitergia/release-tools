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
#     Venu Vardhan Reddy Tekula <venu@bitergia.com>
#

import os
import subprocess


class RepositoryError(Exception):
    """Generic repository error class."""
    pass


class GitHandler:
    """Class to help to run Git commands."""

    def __init__(self, dirpath=os.getcwd()):
        self.gitenv = {
            'LANG': 'C',
            'PAGER': '',
            'HTTP_PROXY': os.getenv('HTTP_PROXY', ''),
            'HTTPS_PROXY': os.getenv('HTTPS_PROXY', ''),
            'NO_PROXY': os.getenv('NO_PROXY', ''),
            'HOME': os.getenv('HOME', '')
        }
        self.dirpath = dirpath

    @property
    def root_path(self):
        cmd = ['git', 'rev-parse', '--show-toplevel']
        root_path = self._exec(cmd, cwd=self.dirpath, env=self.gitenv).strip('\n')
        return root_path

    def add(self, filename):
        cmd = ['git', 'add', filename]
        self._exec(cmd, cwd=self.dirpath, env=self.gitenv)

    def rm(self, filename):
        cmd = ['git', 'rm', filename]
        self._exec(cmd, cwd=self.dirpath, env=self.gitenv)

    def tag(self, version):
        cmd = ['git', 'tag', '-a', version, '-m', 'Release ' + version]
        self._exec(cmd, cwd=self.dirpath, env=self.gitenv)

    def commit(self, msg, author):
        cmd = ['git', 'commit', '-m', msg, '--author', author]
        self._exec(cmd, cwd=self.dirpath, env=self.gitenv)

    def push(self, remote, ref):
        cmd = ['git', 'push', remote, ref]
        self._exec(cmd, cwd=self.dirpath, env=self.gitenv)

    def reset_head(self):
        cmd = ['git', 'reset', 'HEAD^']
        self._exec(cmd, cwd=self.dirpath, env=self.gitenv)

    def restore_staged(self):
        cmd = ['git', 'restore', '--staged', '.']
        self._exec(cmd, cwd=self.dirpath, env=self.gitenv)

    def restore_unstaged(self, dirpath):
        cmd = ['git', 'restore', dirpath]
        self._exec(cmd, cwd=self.dirpath, env=self.gitenv)

    def find_file(self, filename):
        """Find a file in the repository.

        Look for a tracked file that matches the given expression
        in the repository. The method returns the path to that
        file if exists; otherwise it returns `None`.

        :param filename: name of the file to look for; wildcards allowed

        :returns: the path to file or `None` when the file does not exist.
        """
        cmd = ['git', 'ls-files', filename]
        filepath = self._exec(cmd, cwd=self.dirpath, env=self.gitenv).strip('\n')

        if not filepath:
            return None
        else:
            return filepath.strip('\n')

    @staticmethod
    def _exec(cmd, cwd=None, env=None):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                cwd=cwd, env=env)
        (outs, errs) = proc.communicate()

        if proc.returncode != 0:
            error = errs.decode('utf-8', errors='surrogateescape')
            msg = "{}; code error: {}".format(error.strip('\n'), proc.returncode)
            raise RepositoryError(msg)

        return outs.decode('utf-8', errors='surrogateescape')
