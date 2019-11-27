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
# along with this program. If not, see <http://www.gnu.org/licenses/>..
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

import unittest

from release_tools.entry import CategoryChange, ChangelogEntry


class TestCategoryChange(unittest.TestCase):
    """Unit tests for CategoryChange"""

    def test_category_attributes(self):
        """Check if the predefined values were intialized"""

        # ADDED category tests
        self.assertEqual(CategoryChange.ADDED.value, 1)
        self.assertEqual(CategoryChange.ADDED.category, 'added')
        self.assertEqual(CategoryChange.ADDED.title, 'New feature')

        # SECURITY category tests
        self.assertEqual(CategoryChange.SECURITY.value, 6)
        self.assertEqual(CategoryChange.SECURITY.category, 'security')
        self.assertEqual(CategoryChange.SECURITY.title, 'Security fix')

        # PERFORMANCE category tests
        self.assertEqual(CategoryChange.PERFORMANCE.value, 7)
        self.assertEqual(CategoryChange.PERFORMANCE.category, 'performance')
        self.assertEqual(CategoryChange.PERFORMANCE.title, 'Performance improvement')

    def test_index(self):
        """Check if predefined indexing works"""

        self.assertEqual(CategoryChange(1), CategoryChange.ADDED)
        self.assertEqual(CategoryChange(2), CategoryChange.FIXED)
        self.assertEqual(CategoryChange(8), CategoryChange.OTHER)

    def test_values(self):
        """Test 'values' class method"""

        expected = [
            'added', 'fixed', 'changed',
            'deprecated', 'removed', 'security',
            'performance', 'other'
        ]

        values = CategoryChange.values()
        self.assertListEqual(values, expected)


class TestChangelogEntry(unittest.TestCase):
    """Unit tests for ChangelogEntry"""

    def test_initialization(self):
        """Check whether class attributes are correctly initialized"""

        entry = ChangelogEntry('new entry', 'fixed', 'jdoe')
        self.assertEqual(entry.title, 'new entry')
        self.assertEqual(entry.category, 'fixed')
        self.assertEqual(entry.author, 'jdoe')
        self.assertEqual(entry.pr, None)
        self.assertEqual(entry.notes, None)

        entry = ChangelogEntry('last entry', 'added', 'jsmith',
                               pr='42', notes="some notes go here")
        self.assertEqual(entry.title, 'last entry')
        self.assertEqual(entry.category, 'added')
        self.assertEqual(entry.author, 'jsmith')
        self.assertEqual(entry.pr, '42')
        self.assertEqual(entry.notes, 'some notes go here')

    def test_to_dict(self):
        """Check if the object is correctly converted into a dict"""

        expected = {
            'title': 'last entry',
            'category': 'added',
            'author': 'jsmith',
            'pull_request': '42',
            'notes': 'some notes go here'
        }

        entry = ChangelogEntry('last entry', 'added', 'jsmith',
                               pr='42', notes="some notes go here")
        self.assertDictEqual(entry.to_dict(), expected)


if __name__ == '__main__':
    unittest.main()
