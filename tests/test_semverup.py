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

import os
import re
import unittest
import unittest.mock

import click.testing
import semver
import tomlkit.toml_file

from release_tools import semverup
from release_tools.entry import CategoryChange
from release_tools.repo import RepositoryError


VERSION_FILE_NOT_FOUND = (
    "Error: version file not found"
)
VERSION_FILE_NOT_EXISTS = (
    r"Error: version file .+_version\.py does not exist"
)
VERSION_NUMBER_NOT_FOUND = (
    r"Error: version number not found"
)
VERSION_NOT_UPDATED = (
    "Error: no changes found; version number not updated"
)
PYPROJECT_FILE_NOT_FOUND = (
    "Error: pyproject file not found"
)
INVALID_VERSION_NUMBER = (
    r"Error: version number 'invalid format' in .+_version\.py is not a valid semver string"
)
CHANGELOG_DIR_NOT_FOUND = (
    r"Error: changelog entries directory .+ does not exist"
)
CHANGELOG_INVALID_ENTRY_ERROR = (
    r"Error: invalid format for .+; 'title' attribute not found"
)
MOCK_REPOSIORY_ERROR = (
    "Error: mock repository error"
)


class TestSemVerUp(unittest.TestCase):
    """Unit tests for semverup script"""

    @staticmethod
    def setup_files(version_file, project_file, version):
        """Set up files needed for unit tests."""

        TestSemVerUp.setup_version_file(version_file, version)
        TestSemVerUp.setup_pyproject_file(project_file, version)

    @staticmethod
    def setup_version_file(filepath, version):
        """Set up an initial version file with the given version number"""

        with open(filepath, mode='w') as fd:
            fd.write("__version__ = \"{}\"\n".format(version))

    @staticmethod
    def setup_pyproject_file(filepath, version):
        """Set up an initial version value in the pyproject file"""

        with open(filepath, mode='w') as fd:
            fd.write("[tool.poetry]\n")
            fd.write("version = \"{}\"\n".format(version))

    @staticmethod
    def setup_unreleased_entries(dirpath, only_fixed=False):
        """Set up a set of unreleased entry files"""

        titles = ['first change', 'next change', 'last change']

        if only_fixed:
            categories = [
                CategoryChange.FIXED,
                CategoryChange.FIXED,
                CategoryChange.FIXED
            ]
        else:
            categories = [
                CategoryChange.ADDED,
                CategoryChange.FIXED,
                CategoryChange.DEPRECATED
            ]

        authors = ['jsmith', 'jdoe', 'jsmith']

        os.makedirs(dirpath)

        # Create some entries
        for x in range(0, 3):
            filepath = os.path.join(dirpath, str(x) + '.yml')

            with open(filepath, mode='w') as fd:
                msg = "---\ntitle: {}\ncategory: {}\n"
                msg += "author: {}\nissue: '{}'\nnotes: null\n"
                msg = msg.format(titles[x], categories[x].category, authors[x], x)
                fd.write(msg)

    @staticmethod
    def setup_major_entry(dirpath):
        filepath = os.path.join(dirpath, 'changed.yml')

        with open(filepath, mode='w') as fd:
            msg = "---\ntitle: {}\ncategory: {}\n"
            msg += "author: {}\nissue: '{}'\nnotes: null\n"
            msg = msg.format("major change", CategoryChange.CHANGED.category, "jdoe", '4')
            fd.write(msg)

    @staticmethod
    def read_version_number(filepath):
        """Returns the version number stored in a version file"""

        # Check version number
        with open(filepath, mode='r') as fd:
            version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                                fd.read(), re.MULTILINE).group(1)
        return version

    @staticmethod
    def read_version_number_from_pyproject(filepath):
        """Returns the version number stored in a pyproject file"""

        fd = tomlkit.toml_file.TOMLFile(filepath)

        metadata = fd.read()
        poetry_metadata = metadata["tool"]["poetry"]

        return poetry_metadata["version"]

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_version_is_updated(self, mock_project):
        """Check whether the version is updated"""

        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            self.setup_files(version_file, project_file, "0.1.0")
            self.setup_unreleased_entries(dirpath)

            # Run the script command
            result = runner.invoke(semverup.semverup)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout, "0.2.0\n")

            version = self.read_version_number(version_file)
            self.assertEqual(version, "0.2.0")

            version = self.read_version_number_from_pyproject(project_file)
            self.assertEqual(version, "0.2.0")

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_dry_run(self, mock_project):
        """Check whether the version file is not updated in dry mode"""

        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            self.setup_files(version_file, project_file, "0.8.10")
            self.setup_unreleased_entries(dirpath)

            # Run the script command
            result = runner.invoke(semverup.semverup, ['--dry-run'])
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout, "0.9.0\n")

            # Version number file did not change
            version = self.read_version_number(version_file)
            self.assertEqual(version, "0.8.10")

            # Pyproject version number did not change either
            version = self.read_version_number_from_pyproject(project_file)
            self.assertEqual(version, "0.8.10")

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_patch_number_is_bumped(self, mock_project):
        """Check whether the patch number is bumped when there are only patch changes"""

        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            self.setup_files(version_file, project_file, "0.8.10")
            self.setup_unreleased_entries(dirpath, only_fixed=True)

            # Run the script command
            result = runner.invoke(semverup.semverup)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout, "0.8.11\n")

            # Version changed in files
            version = self.read_version_number(version_file)
            self.assertEqual(version, "0.8.11")

            version = self.read_version_number_from_pyproject(project_file)
            self.assertEqual(version, "0.8.11")

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_minor_number_is_bumped(self, mock_project):
        """Check whether the minor number is bumped when there are minor and patch changes"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            self.setup_files(version_file, project_file, "0.8.10")
            self.setup_unreleased_entries(dirpath)

            # Run the script command
            result = runner.invoke(semverup.semverup)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout, "0.9.0\n")

            # Version changed in files
            version = self.read_version_number(version_file)
            self.assertEqual(version, "0.9.0")

            version = self.read_version_number_from_pyproject(project_file)
            self.assertEqual(version, "0.9.0")

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_minor_number_is_bumped_in_dev_version(self, mock_project):
        """Check whether the minor number is bumped when there is a major change in dev version"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            self.setup_files(version_file, project_file, "0.8.10")
            self.setup_unreleased_entries(dirpath)
            self.setup_major_entry(dirpath)

            # Run the script command
            result = runner.invoke(semverup.semverup)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout, "0.9.0\n")

            # Version changed in files
            version = self.read_version_number(version_file)
            self.assertEqual(version, "0.9.0")

            version = self.read_version_number_from_pyproject(project_file)
            self.assertEqual(version, "0.9.0")

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_major_number_is_bumped(self, mock_project):
        """Check whether the major number is bumped when there is a major change"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            self.setup_files(version_file, project_file, "1.8.10")
            self.setup_unreleased_entries(dirpath)
            self.setup_major_entry(dirpath)

            # Run the script command
            result = runner.invoke(semverup.semverup)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout, "2.0.0\n")

            # Version changed in files
            version = self.read_version_number(version_file)
            self.assertEqual(version, "2.0.0")

            version = self.read_version_number_from_pyproject(project_file)
            self.assertEqual(version, "2.0.0")

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_version_number_not_bumped_when_empty_changelog_dir(self, mock_project):
        """Check if the version does not change when no changes are available"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            self.setup_files(version_file, project_file, "0.8.10")

            # Create an empty dir
            os.makedirs(dirpath)

            # Run the script command
            result = runner.invoke(semverup.semverup)
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertEqual(lines[-2], VERSION_NOT_UPDATED)

            # Check if the version number did not change
            version = self.read_version_number(version_file)
            self.assertEqual(version, "0.8.10")

            # Pyproject version number did not change either
            version = self.read_version_number_from_pyproject(project_file)
            self.assertEqual(version, "0.8.10")

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_changelog_dir_not_exists_error(self, mock_project):
        """Check if it returns an error when the changelog dir does not exist"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            self.setup_files(version_file, project_file, "0.8.10")

            # Run the script command
            result = runner.invoke(semverup.semverup)
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertRegex(lines[-2], CHANGELOG_DIR_NOT_FOUND)

            # Check if the version number did not change
            version = self.read_version_number(version_file)
            self.assertEqual(version, "0.8.10")

            # Pyproject version number did not change either
            version = self.read_version_number_from_pyproject(project_file)
            self.assertEqual(version, "0.8.10")

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_changelog_invalid_entry_error(self, mock_project):
        """Check if it returns an error when a changelog entry is invalid"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            self.setup_files(version_file, project_file, "0.8.10")
            self.setup_unreleased_entries(dirpath)

            # Create an invalid entry
            entry_fp = os.path.join(dirpath, 'invalid.yml')

            with open(entry_fp, mode='w') as fd:
                msg = "---category: added\n"
                msg += "author: jsmith\nissue: '42'\nnotes: 'some notes go here'\n"
                fd.write(msg)

            # Run the script command
            result = runner.invoke(semverup.semverup)
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertRegex(lines[-2], CHANGELOG_INVALID_ENTRY_ERROR)

            # Check if the version number did not change
            version = self.read_version_number(version_file)
            self.assertEqual(version, "0.8.10")

            # Pyproject version number did not change either
            version = self.read_version_number_from_pyproject(project_file)
            self.assertEqual(version, "0.8.10")

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_repository_error(self, mock_project):
        """Check if it stops working when it encounters RepositoryError exception"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            mock_project.side_effect = RepositoryError('mock repository error')

            # Run the script command
            result = runner.invoke(semverup.semverup)
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertEqual(lines[-2], MOCK_REPOSIORY_ERROR)

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_version_file_not_found(self, mock_project):
        """Check whether it fails when the version file is not found"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            mock_project.return_value.version_file = None

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            self.setup_unreleased_entries(dirpath)

            # Run the script command
            result = runner.invoke(semverup.semverup)
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertEqual(lines[-2], VERSION_FILE_NOT_FOUND)

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_version_file_not_exists(self, mock_project):
        """Check whether it fails when the version file does not exist"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            self.setup_unreleased_entries(dirpath)

            # Run the script command
            result = runner.invoke(semverup.semverup)
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertRegex(lines[-2], VERSION_FILE_NOT_EXISTS)

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_version_not_found(self, mock_project):
        """Check whether it fails when the version string is not found in the file"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            # Write an invalid content
            with open(version_file, mode='w') as fd:
                fd.write("lorem ipsum")

            self.setup_unreleased_entries(dirpath)

            # Run the script command
            result = runner.invoke(semverup.semverup)
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertRegex(lines[-2], VERSION_NUMBER_NOT_FOUND)

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_version_invalid_format(self, mock_project):
        """Check whether it fails when the version file has an invalid format"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            self.setup_version_file(version_file, "invalid format")
            self.setup_unreleased_entries(dirpath)

            # Run the script command
            result = runner.invoke(semverup.semverup)
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertRegex(lines[-2], INVALID_VERSION_NUMBER)

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_pyproject_file_not_found(self, mock_project):
        """Check whether it fails when the pyproject file is not found"""

        runner = click.testing.CliRunner(mix_stderr=False)

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            mock_project.return_value.pyproject_file = None

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            self.setup_version_file(version_file, "0.8.10")
            self.setup_unreleased_entries(dirpath)

            # Run the script command
            result = runner.invoke(semverup.semverup)
            self.assertEqual(result.exit_code, 1)

            lines = result.stderr.split('\n')
            self.assertEqual(lines[-2], PYPROJECT_FILE_NOT_FOUND)

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_force_version_number_argument(self, mock_project):
        """Check if it increases the version number passed by argument"""

        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            self.setup_files(version_file, project_file, "0.8.10")

            # Run the script command for major
            result = runner.invoke(semverup.semverup, ['--bump-version', 'major'])
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout, "1.0.0\n")

            # Version changed in files
            version = self.read_version_number(version_file)
            self.assertEqual(version, "1.0.0")

            version = self.read_version_number_from_pyproject(project_file)
            self.assertEqual(version, "1.0.0")

            # Run the script command for minor
            result = runner.invoke(semverup.semverup, ['--bump-version', 'minor'])
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout, "1.1.0\n")

            # Run the script command for patch
            result = runner.invoke(semverup.semverup, ['--bump-version', 'patch'])
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout, "1.1.1\n")

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_entries_and_prerelease(self, mock_project):
        """
        Check when calling semverup with changelog entries and --pre-release,
        a release candidate is generated
        """
        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            self.setup_files(version_file, project_file, "0.8.10")
            self.setup_unreleased_entries(dirpath, only_fixed=True)

            # Run the script command
            result = runner.invoke(semverup.semverup, args=['--pre-release'])
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout, "0.8.11-rc.1\n")

            # Version changed in files
            version = self.read_version_number(version_file)
            self.assertEqual(version, "0.8.11-rc.1")

            version = self.read_version_number_from_pyproject(project_file)
            self.assertEqual(version, "0.8.11-rc.1")

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_rc_entries_and_prerelease(self, mock_project):
        """
        Check when calling semverup with changelog entries, --pre-release option and
        a pre-release version number, the release candidate number is updated
        """
        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath
            mock_project.return_value.unreleased_processed_entries_path = os.path.join(dirpath, 'processed')

            self.setup_files(version_file, project_file, "0.8.10-rc.1")
            self.setup_unreleased_entries(dirpath, only_fixed=True)

            # Run the script command
            result = runner.invoke(semverup.semverup, args=['--pre-release'])
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout, "0.8.10-rc.2\n")

            # Version changed in files
            version = self.read_version_number(version_file)
            self.assertEqual(version, "0.8.10-rc.2")

            version = self.read_version_number_from_pyproject(project_file)
            self.assertEqual(version, "0.8.10-rc.2")

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_rc_no_entries_and_prerelease(self, mock_project):
        """
        Check when calling semverup without changelog entries, --pre-release option and
        a pre-release version number, the command fails
        """
        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            self.setup_files(version_file, project_file, "0.8.10-rc.1")

            # Run the script command
            result = runner.invoke(semverup.semverup, args=['--pre-release'])
            self.assertEqual(result.exit_code, 1)

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_force_version_prerelease(self, mock_project):
        """
        Check when calling semverup with --bump-version and --pre-release options,
        a release candidate is created
        """
        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            self.setup_files(version_file, project_file, "0.8.10")

            # Run the script command for major
            result = runner.invoke(semverup.semverup, ['--bump-version', 'major', '--pre-release'])
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout, "1.0.0-rc.1\n")

            # Version changed in files
            version = self.read_version_number(version_file)
            self.assertEqual(version, "1.0.0-rc.1")

            version = self.read_version_number_from_pyproject(project_file)
            self.assertEqual(version, "1.0.0-rc.1")

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_rc_force_version_prerelease(self, mock_project):
        """
        Check when calling semverup with --bump-version and --pre-release options, and
        the version is a pre-release, rc's number is increased
        """

        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            self.setup_files(version_file, project_file, "1.0.0-rc.1")

            # Run the script command for major
            result = runner.invoke(semverup.semverup, ['--bump-version', 'major', '--pre-release'])
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout, "1.0.0-rc.2\n")

            # Version changed in files
            version = self.read_version_number(version_file)
            self.assertEqual(version, "1.0.0-rc.2")

            version = self.read_version_number_from_pyproject(project_file)
            self.assertEqual(version, "1.0.0-rc.2")

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_remove_prerelease_part(self, mock_project):
        """Check whether the pre-release metadata is removed when
        '--pre-release' option is not provided"""

        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            dirpath = os.path.join(fs, 'releases', 'unreleased')
            mock_project.return_value.unreleased_changes_path = dirpath

            self.setup_files(version_file, project_file, "0.8.10-rc.1")
            self.setup_unreleased_entries(dirpath, only_fixed=True)

            # Run the script command
            result = runner.invoke(semverup.semverup)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout, "0.8.10\n")

            # Version changed in files
            version = self.read_version_number(version_file)
            self.assertEqual(version, "0.8.10")

            version = self.read_version_number_from_pyproject(project_file)
            self.assertEqual(version, "0.8.10")

    @unittest.mock.patch('release_tools.semverup.Project')
    def test_remove_prerelease_part_force_version(self, mock_project):
        """Check whether the pre-release metadata is removed when
        only '--bump-version' option is provided"""

        runner = click.testing.CliRunner()

        with runner.isolated_filesystem() as fs:
            version_file = os.path.join(fs, '_version.py')
            mock_project.return_value.version_file = version_file

            project_file = os.path.join(fs, 'pyproject.toml')
            mock_project.return_value.pyproject_file = project_file

            self.setup_files(version_file, project_file, "0.8.10-rc.1")

            # Run the script command
            result = runner.invoke(semverup.semverup, args=['--bump-version=PATCH'])
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.stdout, "0.8.10\n")

            # Version changed in files
            version = self.read_version_number(version_file)
            self.assertEqual(version, "0.8.10")

            version = self.read_version_number_from_pyproject(project_file)
            self.assertEqual(version, "0.8.10")

    def test_get_next_version(self):
        """Check multiple version changes based on inputs"""

        # arg__version, arg_bump_version, arg_prerelease, expected
        test_cases = [
            ('1.1.3', 'PATCH', False, '1.1.4'),
            ('1.1.3', 'MINOR', False, '1.2.0'),
            ('1.1.3', 'MAJOR', False, '2.0.0'),
            ('0.0.1', 'PATCH', True, '0.0.2-rc.1'),
            ('0.0.1', 'MINOR', True, '0.1.0-rc.1'),
            ('0.0.1', 'MAJOR', True, '1.0.0-rc.1'),
            ('0.1.0', 'PATCH', True, '0.1.1-rc.1'),
            ('0.1.0', 'MINOR', True, '0.2.0-rc.1'),
            ('0.1.0', 'MAJOR', True, '1.0.0-rc.1'),
            ('1.0.2-rc.1', 'PATCH', True, '1.0.2-rc.2'),
            ('1.0.2-rc.1', 'MINOR', True, '1.1.0-rc.1'),
            ('1.0.2-rc.1', 'MAJOR', True, '2.0.0-rc.1'),
            ('1.2.0-rc.1', 'PATCH', True, '1.2.0-rc.2'),
            ('1.2.0-rc.1', 'MINOR', True, '1.2.0-rc.2'),
            ('1.2.0-rc.1', 'MAJOR', True, '2.0.0-rc.1'),
            ('1.0.0-rc.1', 'PATCH', True, '1.0.0-rc.2'),
            ('1.0.0-rc.1', 'MINOR', True, '1.0.0-rc.2'),
            ('1.0.0-rc.1', 'MAJOR', True, '1.0.0-rc.2'),
            ('1.1.0-rc.1', 'PATCH', False, '1.1.0'),
            ('1.1.0-rc.1', 'MINOR', False, '1.1.0'),
            ('1.1.0-rc.1', 'MAJOR', False, '2.0.0'),
            ('1.1.0-rc.1', None, False, '1.1.0'),
        ]
        tests_no_changes = [
            ('1.1.0', None, True),
            ('1.1.3', None, False),
            ('1.1.0-rc.1', None, True),
        ]
        for case in test_cases:
            in_version = semver.VersionInfo.parse(case[0])
            version = semverup.get_next_version(current_version=in_version,
                                                bump_version=case[1],
                                                do_prerelease=case[2])
            self.assertEqual(str(version), case[3])

        for case in tests_no_changes:
            with self.assertRaisesRegex(click.ClickException, "no changes found; version number not updated"):
                in_version = semver.VersionInfo.parse(case[0])
                _ = semverup.get_next_version(current_version=in_version,
                                              bump_version=case[1],
                                              do_prerelease=case[2])


if __name__ == '__main__':
    unittest.main()
