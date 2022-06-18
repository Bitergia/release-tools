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
#     Venu Vardhan Reddy Tekula <venu@bitergia.com>
#

import datetime
import os
import unittest
import unittest.mock

import click.testing

from release_tools.notes import notes, ReleaseNotesComposer
from release_tools.entry import CategoryChange
from release_tools.repo import RepositoryError


RELEASE_NOTES_CONTENT = """## release-tools 0.8.10 - (2019-01-01)

**New features:**

 * first feature (#1)\\
   Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
   eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad
   minim veniam, quis nostrud exercitation ullamco laboris nisi ut
   aliquip ex ea commodo consequat. Duis aute irure dolor in
   reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
   pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
   culpa qui officia deserunt mollit anim id est laborum.
 * second feature (#3)
 * final feature

**Bug fixes:**

 * first bug fix (#2)
 * another fix\\
   Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
   eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad
   minim veniam, quis nostrud exercitation ullamco laboris nisi ut
   aliquip ex ea commodo consequat. Duis aute irure dolor in
   reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla
   pariatur. Excepteur sint occaecat cupidatat non proident, sunt in
   culpa qui officia deserunt mollit anim id est laborum.

"""
RELEASE_NOTES_EMPTY = """## release-tools 0.8.10 - (2019-01-01)

No changes list available.

"""
NEWS_FILE_ORIGINAL_CONTENT = """# Releases

## release-tools 0.1 - (1900-01-01)

Initial release
"""
NEWS_FILE_CONTENT = """# Releases\n\n""" + RELEASE_NOTES_CONTENT + NEWS_FILE_ORIGINAL_CONTENT[11:] + "\n"

AUTHORS_FILE_ORIGINAL_CONTENT = """jdoe\n\n"""
AUTHORS_FILE_ORIGINAL_CONTENT_NO_NEW_LINE = """jdoe"""
AUTHORS_FILE_CONTENT = """jdoe\njsmith\njwick\n\n"""
RELEASE_NOTES_FILE_ALREADY_EXISTS_ERROR = (
    "Error: Release notes for version 0.8.10 already exist. Use '--overwrite' to replace it."
)
EMPTY_CONTENT_ERROR = (
    "Error: Aborting due to empty release notes"
)
INVALID_CHANGELOG_ENTRY_ERROR = (
    "Error: Invalid changelog entry format"
)
CHANGELOG_DIR_NOT_FOUND_ERROR = (
    r"Error: changelog entries directory '.+' does not exist"
)
INVALID_NAME_ERROR = (
    "Error: Invalid value for \"|\'NAME\"|\': cannot be empty"
)
INVALID_VERSION_ERROR = (
    "Error: Invalid value for \"|\'VERSION\"|\': cannot be empty"
)
MOCK_REPOSITORY_ERROR = (
    "Error: fatal: not a git repository (or any of the parent directories): .git; code error: 128"
)


class TestNotes(unittest.TestCase):
    """Unit tests for notes script"""

    @staticmethod
    def setup_unreleased_entries(dirpath):
        """Set up a set of unreleased entry files"""

        titles = [
            "first feature",
            "first bug fix",
            "second feature",
            "final feature",
            "another fix",
        ]
        categories = [
            CategoryChange.ADDED,
            CategoryChange.FIXED,
            CategoryChange.ADDED,
            CategoryChange.ADDED,
            CategoryChange.FIXED,
        ]
        authors = ['jsmith', 'jdoe', '\n- jsmith\n- jdoe\n- jwick', 'jdoe', 'jsmith']
        issues = [1, 2, 3, 'null', 'null']
        notes = [True, False, False, False, True]
        notes_txt = (
            ">\n"
            "  Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor"
            " incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,"
            " quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo"
            " consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse\n"
            "  cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat"
            " non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
        )

        os.makedirs(dirpath)

        # Create some entries
        for x in range(0, 5):
            filepath = os.path.join(dirpath, str(x) + '.yml')

            with open(filepath, mode='w') as fd:
                msg = "---\ntitle: {}\ncategory: {}\n"
                msg += "author: {}\nissue: {}\nnotes: {}\n"
                ntxt = notes_txt if notes[x] else "null"
                msg = msg.format(titles[x], categories[x].category, authors[x],
                                 issues[x], ntxt)
                fd.write(msg)

    @staticmethod
    def setup_news_file(filepath):
        """Set up a news file"""

        with open(filepath, mode='w') as fd:
            fd.write(NEWS_FILE_ORIGINAL_CONTENT)

    @staticmethod
    def setup_authors_file(filepath):
        """Set up an authors file"""

        with open(filepath, mode='w') as fd:
            fd.write(AUTHORS_FILE_ORIGINAL_CONTENT)

    @staticmethod
    def setup_authors_file_no_new_line(filepath):
        """Set up an authors file"""

        with open(filepath, mode='w') as fd:
            fd.write(AUTHORS_FILE_ORIGINAL_CONTENT_NO_NEW_LINE)

    @unittest.mock.patch('release_tools.notes.ReleaseNotesComposer._datetime_utcnow_str')
    @unittest.mock.patch('release_tools.notes.Project')
    def test_release_notes(self, mock_project, mock_utcnow):
        """Check if it generates a release notes file"""

        mock_utcnow.return_value = "2019-01-01"

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            changes_path = os.path.join(fs, 'releases', 'unreleased')
            news_file = os.path.join(fs, 'NEWS')
            self.setup_unreleased_entries(changes_path)
            self.setup_news_file(news_file)

            mock_project.return_value.basepath = fs
            mock_project.return_value.unreleased_changes_path = changes_path

            # Run the script command
            result = runner.invoke(notes, ['release-tools', '0.8.10'])
            self.assertEqual(result.exit_code, 0)

            filepath = os.path.join(fs, 'releases', '0.8.10.md')
            with open(filepath, 'r') as fd:
                text = fd.read()

            self.assertEqual(text, RELEASE_NOTES_CONTENT)

            with open(news_file, 'r') as fd:
                text = fd.read()

            self.assertEqual(text, NEWS_FILE_ORIGINAL_CONTENT)

    @unittest.mock.patch('release_tools.changelog.Project')
    def test_entry_repository_error(self, mock_project):
        """Check if it stops working when it encounters RepositoryError exception"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            changes_path = os.path.join(fs, 'releases', 'unreleased')
            self.setup_unreleased_entries(changes_path)

            mock_project.side_effect = RepositoryError()

            # Run the script command
            result = runner.invoke(notes, ['release-tools', '0.8.10'])
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertEqual(lines[-2], MOCK_REPOSITORY_ERROR)

            filepath = os.path.join(fs, 'releases', '0.8.10.md')
            self.assertEqual(os.path.exists(filepath), False)

    @unittest.mock.patch('release_tools.notes.ReleaseNotesComposer._datetime_utcnow_str')
    @unittest.mock.patch('release_tools.notes.Project')
    def test_dry_run(self, mock_project, mock_utcnow):
        """Check if it composes the release notes but does not create a file"""

        mock_utcnow.return_value = "2019-01-01"

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            changes_path = os.path.join(fs, 'releases', 'unreleased')
            self.setup_unreleased_entries(changes_path)

            mock_project.return_value.basepath = fs
            mock_project.return_value.unreleased_changes_path = changes_path

            # Run the script command
            result = runner.invoke(notes, ['--dry-run', 'release-tools', '0.8.10'])
            self.assertEqual(result.exit_code, 0)

            filepath = os.path.join(fs, 'releases', '0.8.10.md')
            self.assertEqual(os.path.exists(filepath), False)

            self.assertEqual(result.stdout, RELEASE_NOTES_CONTENT + '\n')

    @unittest.mock.patch('release_tools.notes.ReleaseNotesComposer._datetime_utcnow_str')
    @unittest.mock.patch('release_tools.notes.Project')
    def test_news_update(self, mock_project, mock_utcnow):
        """Check if it updates the news file when the flag is set"""

        mock_utcnow.return_value = "2019-01-01"

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            changes_path = os.path.join(fs, 'releases', 'unreleased')
            news_file = os.path.join(fs, 'NEWS')
            self.setup_unreleased_entries(changes_path)
            self.setup_news_file(news_file)

            mock_project.return_value.basepath = fs
            mock_project.return_value.unreleased_changes_path = changes_path
            mock_project.return_value.news_file = news_file

            # Run the script command
            result = runner.invoke(notes, ['--news', 'release-tools', '0.8.10'])
            self.assertEqual(result.exit_code, 0)

            filepath = os.path.join(fs, 'releases', '0.8.10.md')
            with open(filepath, 'r') as fd:
                text = fd.read()

            self.assertEqual(text, RELEASE_NOTES_CONTENT)

            with open(news_file, 'r') as fd:
                text = fd.read()

            self.assertEqual(text, NEWS_FILE_CONTENT)

    @unittest.mock.patch('release_tools.notes.Project')
    def test_authors_update(self, mock_project):
        """Check if it updates the authors file when the flag is set"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            changes_path = os.path.join(fs, 'releases', 'unreleased')
            authors_file = os.path.join(fs, 'AUTHORS')
            self.setup_unreleased_entries(changes_path)
            self.setup_authors_file(authors_file)

            mock_project.return_value.basepath = fs
            mock_project.return_value.unreleased_changes_path = changes_path
            mock_project.return_value.authors_file = authors_file

            # Run the script command
            result = runner.invoke(notes, ['--authors', 'release-tools', '0.8.10'])
            self.assertEqual(result.exit_code, 0)

            with open(authors_file, 'r') as fd:
                text = fd.read()

            self.assertEqual(text, AUTHORS_FILE_CONTENT)

    @unittest.mock.patch('release_tools.notes.Project')
    def test_authors_update_no_new_line(self, mock_project):
        """Check if it updates the authors file when the flag is set"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            changes_path = os.path.join(fs, 'releases', 'unreleased')
            authors_file = os.path.join(fs, 'AUTHORS')
            self.setup_unreleased_entries(changes_path)
            self.setup_authors_file_no_new_line(authors_file)

            mock_project.return_value.basepath = fs
            mock_project.return_value.unreleased_changes_path = changes_path
            mock_project.return_value.authors_file = authors_file

            # Run the script command
            result = runner.invoke(notes, ['--authors', 'release-tools', '0.8.10'])
            self.assertEqual(result.exit_code, 0)

            with open(authors_file, 'r') as fd:
                text = fd.read()

            self.assertEqual(text, AUTHORS_FILE_CONTENT)

    @unittest.mock.patch('release_tools.notes.ReleaseNotesComposer._datetime_utcnow_str')
    @unittest.mock.patch('release_tools.notes.Project')
    def test_news_empty_file(self, mock_project, mock_utcnow):
        """Check if it creates a news file when it does not exist"""

        mock_utcnow.return_value = "2019-01-01"

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            changes_path = os.path.join(fs, 'releases', 'unreleased')
            news_file = os.path.join(fs, 'NEWS')
            self.setup_unreleased_entries(changes_path)

            mock_project.return_value.basepath = fs
            mock_project.return_value.unreleased_changes_path = changes_path
            mock_project.return_value.news_file = news_file

            # Run the script command
            result = runner.invoke(notes, ['--news', 'release-tools', '0.8.10'])
            self.assertEqual(result.exit_code, 0)

            filepath = os.path.join(fs, 'releases', '0.8.10.md')
            with open(filepath, 'r') as fd:
                text = fd.read()

            self.assertEqual(text, RELEASE_NOTES_CONTENT)

            with open(news_file, 'r') as fd:
                text = fd.read()

            expected = "# Releases\n\n" + RELEASE_NOTES_CONTENT
            self.assertEqual(text, expected)

    @unittest.mock.patch('release_tools.notes.Project')
    def test_authors_empty_file(self, mock_project):
        """Check if it creates an authors file when it does not exist"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            changes_path = os.path.join(fs, 'releases', 'unreleased')
            authors_file = os.path.join(fs, 'AUTHORS')
            self.setup_unreleased_entries(changes_path)

            mock_project.return_value.basepath = fs
            mock_project.return_value.unreleased_changes_path = changes_path
            mock_project.return_value.authors_file = authors_file

            # Run the script command
            result = runner.invoke(notes, ['--authors', 'release-tools', '0.8.10'])
            self.assertEqual(result.exit_code, 0)

            with open(authors_file, 'r') as fd:
                text = fd.read()

            expected = """jsmith\njdoe\njwick\n\n"""
            self.assertEqual(text, expected)

    @unittest.mock.patch('release_tools.notes.ReleaseNotesComposer._datetime_utcnow_str')
    @unittest.mock.patch('release_tools.notes.Project')
    def test_release_notes_no_entry_files(self, mock_project, mock_utcnow):
        """Check if it generates a release notes file when there are not entry files"""

        mock_utcnow.return_value = "2019-01-01"

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            changes_path = os.path.join(fs, 'releases', 'unreleased')
            os.makedirs(changes_path)

            mock_project.return_value.basepath = fs
            mock_project.return_value.unreleased_changes_path = changes_path

            # Run the script command
            result = runner.invoke(notes, ['release-tools', '0.8.10'])
            self.assertEqual(result.exit_code, 0)

            filepath = os.path.join(fs, 'releases', '0.8.10.md')
            with open(filepath, 'r') as fd:
                text = fd.read()

            self.assertEqual(text, RELEASE_NOTES_EMPTY)

    @unittest.mock.patch('release_tools.notes.ReleaseNotesComposer._datetime_utcnow_str')
    @unittest.mock.patch('release_tools.notes.Project')
    def test_release_notes_file_is_not_overwritten(self, mock_project, mock_utcnow):
        """Check whether an existing release notes file is not replaced"""

        mock_utcnow.return_value = "2019-01-01"

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            changes_path = os.path.join(fs, 'releases', 'unreleased')
            self.setup_unreleased_entries(changes_path)

            mock_project.return_value.basepath = fs
            mock_project.return_value.unreleased_changes_path = changes_path

            # Create a file first
            result = runner.invoke(notes, ['release-tools', '0.8.10'])
            self.assertEqual(result.exit_code, 0)

            # Try to replace it with an empty version
            for filename in os.listdir(changes_path):
                filepath = os.path.join(changes_path, filename)
                os.remove(filepath)

            result = runner.invoke(notes, ['release-tools', '0.8.10'])
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertEqual(lines[-2], RELEASE_NOTES_FILE_ALREADY_EXISTS_ERROR)

            # The file did not change
            filepath = os.path.join(fs, 'releases', '0.8.10.md')
            with open(filepath, 'r') as fd:
                text = fd.read()

            self.assertEqual(text, RELEASE_NOTES_CONTENT)

    @unittest.mock.patch('release_tools.notes.ReleaseNotesComposer._datetime_utcnow_str')
    @unittest.mock.patch('release_tools.notes.Project')
    def test_overwrite_release_notes_file(self, mock_project, mock_utcnow):
        """Check whether an existing release notes file is not replaced"""

        mock_utcnow.return_value = "2019-01-01"

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            changes_path = os.path.join(fs, 'releases', 'unreleased')
            self.setup_unreleased_entries(changes_path)

            mock_project.return_value.basepath = fs
            mock_project.return_value.unreleased_changes_path = changes_path

            # Create a file first
            result = runner.invoke(notes, ['release-tools', '0.8.10'])
            self.assertEqual(result.exit_code, 0)

            # Try to replace it with an empty version
            for filename in os.listdir(changes_path):
                filepath = os.path.join(changes_path, filename)
                os.remove(filepath)

            result = runner.invoke(notes, ['--overwrite', 'release-tools', '0.8.10'])
            self.assertEqual(result.exit_code, 0)

            filepath = os.path.join(fs, 'releases', '0.8.10.md')
            with open(filepath, 'r') as fd:
                text = fd.read()

            self.assertEqual(text, RELEASE_NOTES_EMPTY)

    @unittest.mock.patch('release_tools.notes.compose_release_notes')
    @unittest.mock.patch('release_tools.notes.Project')
    def test_abort_empty_notes(self, mock_project, mock_compose):
        """Check if it stops the process when the content of release notes is empty"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            changes_path = os.path.join(fs, 'releases', 'unreleased')
            self.setup_unreleased_entries(changes_path)

            mock_project.return_value.basepath = fs
            mock_project.return_value.unreleased_changes_path = changes_path

            # Force to return an empty content
            mock_compose.return_value = ""

            result = runner.invoke(notes, ['release-tools', '0.8.10'])
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertEqual(lines[-2], EMPTY_CONTENT_ERROR)

    @unittest.mock.patch('release_tools.notes.read_changelog_entries')
    @unittest.mock.patch('release_tools.notes.Project')
    def test_error_reading_entries(self, mock_project, mock_read_entries):
        """Check if it stops the process when there is an error reading changelog entries"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            changes_path = os.path.join(fs, 'releases', 'unreleased')
            self.setup_unreleased_entries(changes_path)

            mock_project.return_value.basepath = fs
            mock_project.return_value.unreleased_changes_path = changes_path

            # Force to return an error when reading the entries
            mock_read_entries.side_effect = Exception("Invalid changelog entry format")

            result = runner.invoke(notes, ['release-tools', '0.8.10'])
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertEqual(lines[-2], INVALID_CHANGELOG_ENTRY_ERROR)

    @unittest.mock.patch('release_tools.notes.Project')
    def test_changelog_dir_not_exists_error(self, mock_project):
        """Check if it returns an error when the changelog dir does not exist"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            changes_path = os.path.join(fs, 'releases', 'unreleased')

            mock_project.return_value.basepath = fs
            mock_project.return_value.unreleased_changes_path = changes_path

            # Run the script command
            result = runner.invoke(notes, ['release-tools', '0.8.10'])
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertRegex(lines[-2], CHANGELOG_DIR_NOT_FOUND_ERROR)

    @unittest.mock.patch('release_tools.notes.datetime')
    def test_datetime_utcnow_str(self, mock_datetime):
        """Check if the correct formatted string of the datetime is returned"""

        mock_datetime.datetime.utcnow.return_value = datetime.datetime(2019, 1, 1)
        result = ReleaseNotesComposer._datetime_utcnow_str()
        self.assertEqual(result, '2019-01-01')

    def test_invalid_name(self):
        """Check whether name argument is validated correctly"""

        runner = click.testing.CliRunner(mix_stderr=False)

        # Empty titles are not allowed
        result = runner.invoke(notes, [''])
        self.assertEqual(result.exit_code, 2)

        lines = result.stderr.split('\n')
        self.assertRegex(lines[-2], INVALID_NAME_ERROR)

        # Only whitespaces are not allowed
        result = runner.invoke(notes, [' '])
        self.assertEqual(result.exit_code, 2)

        lines = result.stderr.split('\n')
        self.assertRegex(lines[-2], INVALID_NAME_ERROR)

        # Only control characters are not allowed
        result = runner.invoke(notes, ['\n\r\n'])
        self.assertEqual(result.exit_code, 2)
        self.assertRegex(lines[-2], INVALID_NAME_ERROR)

    def test_invalid_version(self):
        """Check whether version argument is validated correctly"""

        runner = click.testing.CliRunner(mix_stderr=False)

        # Empty titles are not allowed
        result = runner.invoke(notes, ['release-tools', ''])
        self.assertEqual(result.exit_code, 2)

        lines = result.stderr.split('\n')
        self.assertRegex(lines[-2], INVALID_VERSION_ERROR)

        # Only whitespaces are not allowed
        result = runner.invoke(notes, ['release-tools', ' '])
        self.assertEqual(result.exit_code, 2)

        lines = result.stderr.split('\n')
        self.assertRegex(lines[-2], INVALID_VERSION_ERROR)

        # Only control characters are not allowed
        result = runner.invoke(notes, ['release-tools', '\n\r\n'])
        self.assertEqual(result.exit_code, 2)
        self.assertRegex(lines[-2], INVALID_VERSION_ERROR)


if __name__ == '__main__':
    unittest.main()
