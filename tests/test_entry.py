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
# along with this program. If not, see <http://www.gnu.org/licenses/>..
#
# Authors:
#     Santiago Dueñas <sduenas@bitergia.com>
#

import os
import tempfile
import unittest
import unittest.mock

from release_tools.entry import (CategoryChange,
                                 ChangelogEntry,
                                 read_changelog_entries,
                                 determine_filepath)


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
        self.assertEqual(CategoryChange(9), CategoryChange.OTHER)

    def test_values(self):
        """Test 'values' class method"""

        expected = [
            'added', 'fixed', 'changed',
            'deprecated', 'removed', 'security',
            'performance', 'dependency', 'other'
        ]

        values = CategoryChange.values()
        self.assertListEqual(values, expected)


class TestChangelogEntry(unittest.TestCase):
    """Unit tests for ChangelogEntry"""

    def test_initialization(self):
        """Check whether class attributes are correctly initialized"""

        entry = ChangelogEntry('new entry', 'fixed', 'jdoe')
        self.assertEqual(entry.title, 'new entry')
        self.assertEqual(entry.category, CategoryChange.FIXED)
        self.assertEqual(entry.author, 'jdoe')
        self.assertEqual(entry.issue, None)
        self.assertEqual(entry.notes, None)

        entry = ChangelogEntry('last entry', 'added', 'jsmith',
                               issue='42', notes="some notes go here")
        self.assertEqual(entry.title, 'last entry')
        self.assertEqual(entry.category, CategoryChange.ADDED)
        self.assertEqual(entry.author, 'jsmith')
        self.assertEqual(entry.issue, '42')
        self.assertEqual(entry.notes, 'some notes go here')

    def test_to_dict(self):
        """Check if the object is correctly converted into a dict"""

        expected = {
            'title': 'last entry',
            'category': 'added',
            'author': 'jsmith',
            'issue': '42',
            'notes': 'some notes go here'
        }

        entry = ChangelogEntry('last entry', 'added', 'jsmith',
                               issue='42', notes="some notes go here")
        self.assertDictEqual(entry.to_dict(), expected)

    def test_import_from_yaml_file(self):
        """Check if it imports an entry from a YAML file"""

        with tempfile.NamedTemporaryFile() as f:
            f.write(b"---\ntitle: last entry\ncategory: added\n")
            f.write(b"author: jsmith\nissue: '42'\nnotes: 'some notes go here'\n")
            f.seek(0)

            expected = {
                'title': 'last entry',
                'category': 'added',
                'author': 'jsmith',
                'issue': '42',
                'notes': 'some notes go here'
            }

            entry = ChangelogEntry.from_yaml_file(f.name)
            self.assertDictEqual(entry.to_dict(), expected)

    def test_invalid_format_importing_from_yaml_file(self):
        """Check if an error is raised when the entry is invalid"""

        with tempfile.NamedTemporaryFile() as f:
            # The tittle is missing on this file
            f.write(b"---category: added\n")
            f.write(b"author: jsmith\nissue: '42'\nnotes: 'some notes go here'\n")
            f.seek(0)

            with self.assertRaisesRegex(Exception, "'title' attribute not found"):
                ChangelogEntry.from_yaml_file(f.name)


class TestReadChangelogEntries(unittest.TestCase):
    """Unit tests for read_changelog_entries function"""

    def test_read_entries(self):
        """Check if it imports a set of entries"""

        titles = ['first change', 'next change', 'last change']
        categories = [
            CategoryChange.ADDED,
            CategoryChange.FIXED,
            CategoryChange.DEPRECATED
        ]
        authors = ['jsmith', 'jdoe', 'jsmith']

        with tempfile.TemporaryDirectory() as dirpath:
            # Create some entries
            for x in range(0, 3):
                filepath = os.path.join(dirpath, str(x) + '.yml')

                with open(filepath, mode='w') as f:
                    msg = "---\ntitle: {}\ncategory: {}\n"
                    msg += "author: {}\nissue: '{}'\nnotes: null\n"
                    msg = msg.format(titles[x], categories[x].category, authors[x], x)
                    f.write(msg)

            # This non-yml file is not read
            filepath = os.path.join(dirpath, 'no-yml.txt')

            with open(filepath, mode='w') as f:
                f.write("no YAML file")

            # Import the entries
            entries = read_changelog_entries(dirpath)
            self.assertEqual(len(entries), 3)

            entry = entries['0.yml']
            self.assertEqual(entry.title, 'first change')
            self.assertEqual(entry.category, CategoryChange.ADDED)
            self.assertEqual(entry.author, 'jsmith')
            self.assertEqual(entry.issue, '0')
            self.assertEqual(entry.notes, None)

            entry = entries['1.yml']
            self.assertEqual(entry.title, 'next change')
            self.assertEqual(entry.category, CategoryChange.FIXED)
            self.assertEqual(entry.author, 'jdoe')
            self.assertEqual(entry.issue, '1')
            self.assertEqual(entry.notes, None)

            entry = entries['2.yml']
            self.assertEqual(entry.title, 'last change')
            self.assertEqual(entry.category, CategoryChange.DEPRECATED)
            self.assertEqual(entry.author, 'jsmith')
            self.assertEqual(entry.issue, '2')
            self.assertEqual(entry.notes, None)

    def test_read_entries_empty_dir(self):
        """Check if nothing is imported when reading an empty directory"""

        with tempfile.TemporaryDirectory() as dirpath:
            entries = read_changelog_entries(dirpath)
            self.assertDictEqual(entries, {})


class TestDetermineFilePath(unittest.TestCase):
    """Unit tests for determine_filepath"""

    def test_filepath(self):
        """Check it the right filepath is returned"""

        dirpath = "/tmp/repo/releases/unreleased/"
        expected = os.path.join(dirpath, "my-change.yml")

        filepath = determine_filepath(dirpath, "my change")
        self.assertEqual(filepath, expected)

    def test_random_filepath(self):
        """Check it the right filepath is returned"""

        dirpath = "/tmp/repo/releases/unreleased/"
        expected = os.path.join(dirpath, "releasepublish-my-custom-change.yml")

        filepath = determine_filepath(dirpath, '[release/publish] My "custom" change')
        self.assertEqual(filepath, expected)


if __name__ == '__main__':
    unittest.main()
