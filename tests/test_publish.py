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
import unittest
import unittest.mock

import click.testing

from release_tools import publish
from release_tools.repo import RepositoryError


RELEASE_NOTES_CONTENT = """## release-tools 0.8.10 - (2019-01-01)

No changes list available.

"""
ONLY_PUSH_ERROR = (
    r"Error: '--only-push' flag must be set together with '--push'"
)
CHANGELOG_DIR_NOT_FOUND_ERROR = (
    r"Error: changelog entries directory '.+' does not exist"
)
PYPROJECT_FILE_NOT_FOUND_ERROR = (
    r"Error: pyproject file not found"
)
RELEASE_NOTES_FILE_NOT_FOUND_ERROR = (
    r"Error: release notes file .+0\.8\.10\.md not found"
)
NEWS_FILE_NOT_FOUND_ERROR = (
    r"Error: news file not found"
)
REPOSITORY_ERROR = (
    r"Error: generated mock error"
)
VERSION_FILE_NOT_FOUND_ERROR = (
    r"Error: version file not found"
)


class TestPublish(unittest.TestCase):
    """Unit tests for publish script"""

    @staticmethod
    def setup_release_notes(dirpath, filepath, newsfile=None):
        """Set up the release notes file."""

        os.makedirs(dirpath, exist_ok=True)

        with open(filepath, mode='w') as fd:
            fd.write(RELEASE_NOTES_CONTENT)

        if newsfile:
            with open(newsfile, mode='w') as fd:
                fd.write(RELEASE_NOTES_CONTENT)

    @unittest.mock.patch('release_tools.publish.read_changelog_entries')
    @unittest.mock.patch('release_tools.publish.Project')
    def test_publish(self, mock_project, mock_read_changelog):
        """Test if a new release is published."""

        files = {
            'file1': 'content',
            'file2': 'content',
            'file3': 'content'
        }
        version_number = "0.8.10"

        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            pyproject_file = os.path.join(fs, 'pyproject.toml')
            notes_file = os.path.join(fs, version_number + '.md')
            news_file = os.path.join(fs, 'NEWS')

            self.setup_release_notes(fs, notes_file, newsfile=news_file)

            mock_read_changelog.return_value = files
            mock_project.return_value.unreleased_changes_path = fs
            mock_project.return_value.releases_path = fs
            mock_project.return_value.version_file = version_file
            mock_project.return_value.pyproject_file = pyproject_file
            mock_project.return_value.news_file = news_file

            # Run the command
            result = runner.invoke(publish.publish,
                                   ["0.8.10", "John Smith <jsmith@example.org>"])
            self.assertEqual(result.exit_code, 0)

            # Check mock calls
            mock_project.return_value.repo.add.assert_called()
            mock_project.return_value.repo.rm.assert_called()

            # All files where removed
            for f in files.keys():
                filepath = os.path.join(fs, f)
                mock_project.return_value.repo.rm.assert_any_call(filepath)

            # Version file and notes where added
            mock_project.return_value.repo.add.assert_any_call(version_file)
            mock_project.return_value.repo.add.assert_any_call(pyproject_file)
            mock_project.return_value.repo.add.assert_any_call(notes_file)
            mock_project.return_value.repo.add.assert_any_call(news_file)

            # Commit and tag were only called once
            mock_project.return_value.repo.commit.assert_called_once_with("Release 0.8.10",
                                                                          "John Smith <jsmith@example.org>")
            mock_project.return_value.repo.tag.assert_called_once_with('0.8.10')

            # Push method was not called
            mock_project.return_value.repo.push.assert_not_called()

    @unittest.mock.patch('release_tools.publish.read_changelog_entries')
    @unittest.mock.patch('release_tools.publish.Project')
    def test_publish_to_remote(self, mock_project, mock_read_changelog):
        """Test if a new release is published and pushed to a remote."""

        files = {
            'file1': 'content',
            'file2': 'content',
            'file3': 'content'
        }
        version_number = "0.8.10"

        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            pyproject_file = os.path.join(fs, 'pyproject.toml')
            notes_file = os.path.join(fs, version_number + '.md')
            news_file = os.path.join(fs, 'NEWS')

            self.setup_release_notes(fs, notes_file, newsfile=news_file)

            mock_read_changelog.return_value = files
            mock_project.return_value.unreleased_changes_path = fs
            mock_project.return_value.releases_path = fs
            mock_project.return_value.version_file = version_file
            mock_project.return_value.pyproject_file = pyproject_file
            mock_project.return_value.news_file = news_file

            # Run the command
            result = runner.invoke(publish.publish,
                                   ["--push", "myremote",
                                    "0.8.10", "John Smith <jsmith@example.org>"])
            self.assertEqual(result.exit_code, 0)

            # Check mock calls
            mock_project.return_value.repo.add.assert_called()
            mock_project.return_value.repo.rm.assert_called()

            # All files where removed
            for f in files.keys():
                filepath = os.path.join(fs, f)
                mock_project.return_value.repo.rm.assert_any_call(filepath)

            # Version file and notes where added
            mock_project.return_value.repo.add.assert_any_call(version_file)
            mock_project.return_value.repo.add.assert_any_call(pyproject_file)
            mock_project.return_value.repo.add.assert_any_call(notes_file)
            mock_project.return_value.repo.add.assert_any_call(news_file)

            # Commit and tag were only called once
            mock_project.return_value.repo.commit.assert_called_once_with("Release 0.8.10",
                                                                          "John Smith <jsmith@example.org>")
            mock_project.return_value.repo.tag.assert_called_once_with('0.8.10')

            # Commit and the tag where pushed
            mock_project.return_value.repo.push.assert_any_call('myremote', 'master')
            mock_project.return_value.repo.push.assert_any_call('myremote', '0.8.10')

            # Check non called rollback mock calls
            mock_project.return_value.repo.reset_head.assert_not_called()
            mock_project.return_value.repo.restore_staged.assert_not_called()
            mock_project.return_value.repo.restore_unstaged.assert_not_called()

    @unittest.mock.patch('release_tools.publish.Project')
    def test_only_publish_to_remote(self, mock_project):
        """Test if when '--only-push' is set only tries to push the release commits and tags."""

        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            # Run the command
            result = runner.invoke(publish.publish,
                                   ["--push", "myremote", "--only-push",
                                    "0.8.10", "John Smith <jsmith@example.org>"])
            self.assertEqual(result.exit_code, 0)

            # No other commands than 'push' were called
            mock_project.return_value.repo.add.assert_not_called()
            mock_project.return_value.repo.rm.assert_not_called()
            mock_project.return_value.repo.commit.assert_not_called()
            mock_project.return_value.repo.tag.assert_not_called()

            # Commit and the tag were pushed
            mock_project.return_value.repo.push.assert_any_call('myremote', 'master')
            mock_project.return_value.repo.push.assert_any_call('myremote', '0.8.10')

    @unittest.mock.patch('release_tools.publish.Project')
    def test_only_publish_no_push_error(self, mock_project):
        """Test if fails when '--only-push' is set but not remote is set."""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            # Run the command
            result = runner.invoke(publish.publish,
                                   ["--only-push",
                                    "0.8.10", "John Smith <jsmith@example.org>"])
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertRegex(lines[-2], ONLY_PUSH_ERROR)

            # No commands were called
            mock_project.return_value.repo.add.assert_not_called()
            mock_project.return_value.repo.rm.assert_not_called()
            mock_project.return_value.repo.commit.assert_not_called()
            mock_project.return_value.repo.tag.assert_not_called()
            mock_project.return_value.repo.push.assert_not_called()

    @unittest.mock.patch('release_tools.publish.Project')
    def test_unreleased_dir_not_found_error(self, mock_project):
        """Test if it fails when the unreleased dir is not found."""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            # Run the command
            result = runner.invoke(publish.publish,
                                   ["0.8.10", "John Smith <jsmith@example.org>"])
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertRegex(lines[-2], CHANGELOG_DIR_NOT_FOUND_ERROR)

            # Check non called mock calls not called
            mock_project.return_value.repo.add.assert_not_called()
            mock_project.return_value.repo.rm.assert_not_called()
            mock_project.return_value.repo.commit.assert_not_called()
            mock_project.return_value.repo.tag.assert_not_called()
            mock_project.return_value.repo.push.assert_not_called()

    @unittest.mock.patch('release_tools.publish.read_changelog_entries')
    @unittest.mock.patch('release_tools.publish.Project')
    def test_no_version_file_error(self, mock_project, mock_read_changelog):
        """Test if it fails when the version file does not exist."""

        files = {
            'file1': 'content',
            'file2': 'content',
            'file3': 'content'
        }

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            pyproject_file = os.path.join(fs, 'pyproject.toml')

            mock_read_changelog.return_value = files
            mock_project.return_value.unreleased_changes_path = fs
            mock_project.return_value.releases_path = fs
            mock_project.return_value.version_file = None
            mock_project.return_value.pyproject_file = pyproject_file

            # Run the command
            result = runner.invoke(publish.publish,
                                   ["0.8.10", "John Smith <jsmith@example.org>"])
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertRegex(lines[-2], VERSION_FILE_NOT_FOUND_ERROR)

            # Check called mock calls
            mock_project.return_value.repo.rm.assert_called()

            # Check called rollback mock calls
            mock_project.return_value.repo.restore_staged.assert_called()
            mock_project.return_value.repo.restore_unstaged.assert_called()

            # Check non called mock calls not called
            mock_project.return_value.repo.add.assert_not_called()
            mock_project.return_value.repo.commit.assert_not_called()
            mock_project.return_value.repo.tag.assert_not_called()
            mock_project.return_value.repo.push.assert_not_called()

    @unittest.mock.patch('release_tools.publish.read_changelog_entries')
    @unittest.mock.patch('release_tools.publish.Project')
    def test_no_pyproject_file_error(self, mock_project, mock_read_changelog):
        """Test if it fails when the pyproject file does not exist."""

        files = {
            'file1': 'content',
            'file2': 'content',
            'file3': 'content'
        }

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')

            mock_read_changelog.return_value = files
            mock_project.return_value.unreleased_changes_path = fs
            mock_project.return_value.releases_path = fs
            mock_project.return_value.version_file = version_file
            mock_project.return_value.pyproject_file = None

            # Run the command
            result = runner.invoke(publish.publish,
                                   ["0.8.10", "John Smith <jsmith@example.org>"])
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertRegex(lines[-2], PYPROJECT_FILE_NOT_FOUND_ERROR)

            # Check called mock calls
            mock_project.return_value.repo.rm.assert_called()
            mock_project.return_value.repo.add.assert_called_once_with(version_file)

            # Check called rollback mock calls
            mock_project.return_value.repo.restore_staged.assert_called()
            mock_project.return_value.repo.restore_unstaged.assert_called()

            # Check non called mock calls not called
            mock_project.return_value.repo.commit.assert_not_called()
            mock_project.return_value.repo.tag.assert_not_called()
            mock_project.return_value.repo.push.assert_not_called()

    @unittest.mock.patch('release_tools.publish.read_changelog_entries')
    @unittest.mock.patch('release_tools.publish.Project')
    def test_no_notes_file_error(self, mock_project, mock_read_changelog):
        """Test if it fails when the notes file does not exist."""

        files = {
            'file1': 'content',
            'file2': 'content',
            'file3': 'content'
        }

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            pyproject_file = os.path.join(fs, 'pyproject.toml')

            mock_read_changelog.return_value = files
            mock_project.return_value.unreleased_changes_path = fs
            mock_project.return_value.releases_path = fs
            mock_project.return_value.version_file = version_file
            mock_project.return_value.pyproject_file = pyproject_file

            # Run the command
            result = runner.invoke(publish.publish,
                                   ["0.8.10", "John Smith <jsmith@example.org>"])
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertRegex(lines[-2], RELEASE_NOTES_FILE_NOT_FOUND_ERROR)

            # Check called mock calls
            mock_project.return_value.repo.rm.assert_called()
            mock_project.return_value.repo.add.assert_any_call(version_file)
            mock_project.return_value.repo.add.assert_any_call(pyproject_file)

            # Check called rollback mock calls
            mock_project.return_value.repo.restore_staged.assert_called()
            mock_project.return_value.repo.restore_unstaged.assert_called()

            # Check non called mock calls not called
            mock_project.return_value.repo.commit.assert_not_called()
            mock_project.return_value.repo.tag.assert_not_called()
            mock_project.return_value.repo.push.assert_not_called()

    @unittest.mock.patch('release_tools.publish.read_changelog_entries')
    @unittest.mock.patch('release_tools.publish.Project')
    def test_no_news_file_error(self, mock_project, mock_read_changelog):
        """Test if it fails when the news file does not exist."""

        files = {
            'file1': 'content',
            'file2': 'content',
            'file3': 'content'
        }

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            pyproject_file = os.path.join(fs, 'pyproject.toml')
            notes_file = os.path.join(fs, '0.8.10.md')

            mock_read_changelog.return_value = files
            mock_project.return_value.unreleased_changes_path = fs
            mock_project.return_value.releases_path = fs
            mock_project.return_value.version_file = version_file
            mock_project.return_value.pyproject_file = pyproject_file
            mock_project.return_value.news_file = 'NEWSgit '

            self.setup_release_notes(fs, notes_file)

            # Run the command
            result = runner.invoke(publish.publish,
                                   ["0.8.10", "John Smith <jsmith@example.org>"])
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertRegex(lines[-2], NEWS_FILE_NOT_FOUND_ERROR)

            # Check called mock calls
            mock_project.return_value.repo.rm.assert_called()
            mock_project.return_value.repo.add.assert_any_call(version_file)
            mock_project.return_value.repo.add.assert_any_call(pyproject_file)
            mock_project.return_value.repo.add.assert_any_call(notes_file)

            # Check called rollback mock calls
            mock_project.return_value.repo.restore_staged.assert_called()
            mock_project.return_value.repo.restore_unstaged.assert_called()

            # Check non called mock calls not called
            mock_project.return_value.repo.commit.assert_not_called()
            mock_project.return_value.repo.tag.assert_not_called()
            mock_project.return_value.repo.push.assert_not_called()

    @unittest.mock.patch('release_tools.publish.read_changelog_entries')
    @unittest.mock.patch('release_tools.publish.Project')
    def test_repository_error(self, mock_project, mock_read_changelog):
        """Test if it fails when an error is found in the repository."""

        files = {
            'file1': 'content',
            'file2': 'content',
            'file3': 'content'
        }
        version_number = "0.8.10"

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            pyproject_file = os.path.join(fs, 'pyproject.toml')
            notes_file = os.path.join(fs, version_number + '.md')
            news_file = os.path.join(fs, 'NEWS')

            self.setup_release_notes(fs, notes_file, newsfile=news_file)

            mock_read_changelog.return_value = files
            mock_project.return_value.unreleased_changes_path = fs
            mock_project.return_value.releases_path = fs
            mock_project.return_value.version_file = version_file
            mock_project.return_value.pyproject_file = pyproject_file
            mock_project.return_value.news_file = news_file

            mock_project.return_value.repo.commit.side_effect = RepositoryError("generated mock error")

            # Run the command
            result = runner.invoke(publish.publish,
                                   ["--push", "myremote",
                                    "0.8.10", "John Smith <jsmith@example.org>"])
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertRegex(lines[-2], REPOSITORY_ERROR)

            # Check mock calls
            mock_project.return_value.repo.add.assert_called()
            mock_project.return_value.repo.rm.assert_called()

            # All files where removed
            for f in files.keys():
                filepath = os.path.join(fs, f)
                mock_project.return_value.repo.rm.assert_any_call(filepath)

            # Version file and notes where added
            mock_project.return_value.repo.add.assert_any_call(version_file)
            mock_project.return_value.repo.add.assert_any_call(pyproject_file)
            mock_project.return_value.repo.add.assert_any_call(notes_file)
            mock_project.return_value.repo.add.assert_any_call(news_file)

            # The process failed when commit command was called
            mock_project.return_value.repo.commit.assert_called_once_with("Release 0.8.10",
                                                                          "John Smith <jsmith@example.org>")

            # Check called rollback mock calls
            mock_project.return_value.repo.reset_head.assert_called()
            mock_project.return_value.repo.restore_unstaged.assert_called()

            # Tag and push methods were not called
            mock_project.return_value.repo.tag.assert_not_called()
            mock_project.return_value.repo.push.assert_not_called()


if __name__ == '__main__':
    unittest.main()
