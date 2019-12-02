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

import os
import subprocess


class GitHandler:
    """Class to help to run Git commands."""

    def __init__(self):
        self.gitenv = {
            'LANG': 'C',
            'PAGER': '',
            'HTTP_PROXY': os.getenv('HTTP_PROXY', ''),
            'HTTPS_PROXY': os.getenv('HTTPS_PROXY', ''),
            'NO_PROXY': os.getenv('NO_PROXY', ''),
            'HOME': os.getenv('HOME', '')
        }

    @property
    def root_path(self):
        path_ = self._get_submodule_root_path()

        if not path_:
            basepath = self._get_root_path()

        return basepath

    def _get_root_path(self):
        cmd = ['git', 'rev-parse', '--show-toplevel']
        root_path = self._exec(cmd, env=self.gitenv).strip('\n')
        return root_path

    def _get_submodule_root_path(self):
        cmd = ['git', 'rev-parse', '--show-superproject-working-tree']
        root_path = self._exec(cmd, env=self.gitenv).strip('\n')
        return root_path

    @staticmethod
    def _exec(cmd, cwd=None, env=None):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                cwd=cwd, env=env)
        (outs, errs) = proc.communicate()
        return outs.decode('utf-8', errors='surrogateescape')
