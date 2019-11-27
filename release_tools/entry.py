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
# Note:
#
# This module is based on the work made by GitLab project to generate
# releases automatically. The code is licensed under the terms of the
# MIT license. For more info, please check:
#
#   * https://gitlab.com/gitlab-org/gitlab/blob/master/bin/changelog
#   * https://gitlab.com/gitlab-org/gitlab/blob/master/LICENSE
#

import enum


@enum.unique
class CategoryChange(enum.Enum):
    """Possible category types."""

    def __new__(cls, value, category, title):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.category = category
        obj.title = title
        return obj

    ADDED = (1, 'added', 'New feature')
    FIXED = (2, 'fixed', 'Bug fix')
    CHANGED = (3, 'changed', 'Feature change')
    DEPRECATED = (4, 'deprecated', 'New deprecation')
    REMOVED = (5, 'removed', 'Feature removal')
    SECURITY = (6, 'security', 'Security fix')
    PERFORMANCE = (7, 'performance', 'Performance improvement')
    OTHER = (8, 'other', 'Other')

    @classmethod
    def values(cls):
        return [member.category for member in cls]


class ChangelogEntry:
    """Class to store changelog entries data."""

    def __init__(self, title, category, author, pr=None, notes=None):
        self.title = title
        self.category = category
        self.author = author
        self.pr = pr
        self.notes = notes

    def to_dict(self):
        return {
            'title': self.title,
            'category': self.category,
            'author': self.author,
            'pull_request': self.pr,
            'notes': self.notes
        }