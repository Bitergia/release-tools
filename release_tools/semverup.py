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

"""
Script to increment the version number of a package.

It will bump up the version following the rules defined
by the semantic versioning specification.
"""

import datetime
import os
import re

import click
import semver
import tomlkit.toml_file

from release_tools.entry import read_changelog_entries
from release_tools.project import Project
from release_tools.repo import RepositoryError


VERSION_FILE_TEMPLATE = (
    "# File auto-generated by semverup on {timestamp}\n"
    "__version__ = \"{version}\"\n"
)


@click.command()
@click.option('--dry-run', is_flag=True,
              help="Do not write a new version number. Print to the standard output instead.")
@click.option('--bump-version',
              type=click.Choice(['MAJOR', 'MINOR', 'PATCH'], case_sensitive=False),
              help="Increase only the defined version.")
@click.option('--pre-release', is_flag=True,
              help="Create a new release candidate version.")
def semverup(dry_run, bump_version, pre_release):
    """Increment version number following semver specification.

    This script will bump up the version number of a package in a
    Git repository using semantic versioning.

    You will need to run this script inside that repository. The
    version number must be stored in any directory, under the name
    of '_version.py'. It must also be tracked in the repository.
    New version will be written in the same file. To increase the number
    properly, the script will get the type of every unreleased change
    stored under 'releases/unreleased' directory.

    Additionally, 'pyproject' file will also be updated. Take into
    account this file must be tracked by the repository.

    WARNING: this script does not increase MAJOR version yet
    unless it is forced using --bump-version=major.

    If you don't want to create a new version and see only the final
    result, please active '--dry-run' flag.

    If you want to update the version number regardless the release changes,
    use '--bump-version=[MAJOR,MINOR,PATCH]'.

    If you want to create a release candidate, use '--pre-release'. It can be
    combined with '--bump-version' in case you want to update the version number
    regardless the release changes.

    If the version is a release candidate and '--pre-release' is used, it will
    increase the pre-release part of the version. If '--pre-release' is not used,
    it will remove any pre-release metadata from the version.

    More info about semver specification can be found in the next
    link: https://semver.org/.
    """
    try:
        project = Project(os.getcwd())
    except RepositoryError as e:
        raise click.ClickException(e)

    # Get the current version number
    version_file = find_version_file(project)
    current_version = read_version_number(version_file)

    # Get the pyproject file
    pyproject_file = find_pyproject_file(project)

    # Determine the new version and produce the output
    if bump_version:
        new_version = get_next_version(current_version, bump_version, pre_release)
    else:
        new_version = determine_new_version_number(project, current_version, pre_release)

    if not dry_run:
        write_version_number(version_file, new_version)
        write_version_number_pyproject(pyproject_file,
                                       new_version)

    click.echo(new_version)


def find_version_file(project):
    """Find the version file in the repository."""

    try:
        filepath = project.version_file
    except RepositoryError as e:
        raise click.ClickException(e)

    if not filepath:
        raise click.ClickException("version file not found")

    return filepath


def find_pyproject_file(project):
    """Find the pyproject file in the repository."""

    try:
        filepath = project.pyproject_file
    except RepositoryError as e:
        raise click.ClickException(e)

    if not filepath:
        raise click.ClickException("pyproject file not found")

    return filepath


def read_version_number(filepath):
    """Read the version number of the given file."""

    try:
        with open(filepath, 'r', encoding='utf-8') as fd:
            m = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                          fd.read(), re.MULTILINE)
            if not m:
                raise click.ClickException("version number not found")
            match = m.group(1)
    except FileNotFoundError:
        msg = "version file {} does not exist".format(filepath)
        raise click.ClickException(msg)

    try:
        version = semver.parse_version_info(match)
    except ValueError:
        msg = "version number '{}' in {} is not a valid semver string"
        msg = msg.format(match, filepath)
        raise click.ClickException(msg)

    return version


def get_next_version(current_version, bump_version, do_prerelease=False):
    """Increment version number based on bump_version choice and do_prerelease"""

    if current_version.prerelease:
        next_version = _get_next_version_from_prerelease(current_version, bump_version, do_prerelease)
    else:
        next_version = _get_next_version_from_final_release(current_version, bump_version, do_prerelease)

    if not next_version:
        msg = "no changes found; version number not updated"
        raise click.ClickException(msg)

    return next_version


def _get_next_version_from_prerelease(current_version, bump_version, do_prerelease):
    """Determine the next version number when the current version is a release candidate"""

    next_version = None

    if bump_version == 'MINOR' and current_version.patch != 0:
        # 0.1.1-rc.2 >> 0.2.0(-rc.1)
        next_version = current_version.bump_minor()
    elif bump_version == 'MAJOR' and (current_version.minor != 0 or current_version.patch != 0):
        # 0.1.0-rc.2 >> 1.0.0(-rc.1)
        next_version = current_version.bump_major()

    if do_prerelease:
        if next_version:
            # New version and do prerelease
            next_version = next_version.bump_prerelease()
        elif bump_version:
            # e.g. 0.2.0-rc.1 and minor changelog and do prerelease >> 0.2.0-rc.2
            next_version = current_version.bump_prerelease()
    else:
        # Remove prerelease metadata from the version
        if next_version:
            next_version = next_version.finalize_version()
        else:
            next_version = current_version.finalize_version()

    return next_version


def _get_next_version_from_final_release(current_version, bump_version, do_prerelease):
    """Determine the next version number when the current version is a final release"""

    next_version = None

    if bump_version == 'PATCH':
        # 0.2.0 >> 0.2.1
        next_version = current_version.bump_patch()
    elif bump_version == 'MINOR':
        # 0.2.0 >> 0.3.0
        next_version = current_version.bump_minor()
    elif bump_version == 'MAJOR':
        # 0.2.0 >> 1.0.0
        next_version = current_version.bump_major()

    if next_version and do_prerelease:
        # 0.2.1 >> 0.2.1-rc.1
        next_version = next_version.bump_prerelease()

    return next_version


def determine_new_version_number(project, current_version, prerelease):
    """Guess the next version number."""

    entries = read_unreleased_changelog_entries(project)

    bump_patch = False
    bump_minor = False
    bump_major = False

    for entry in entries.values():
        if entry.category.bump_version == 'major':
            if current_version.major == 0:
                bump_minor = True
            else:
                bump_major = True
            break
        elif entry.category.bump_version == 'minor':
            bump_minor = True
        elif entry.category.bump_version == 'patch':
            bump_patch = True

    if bump_major:
        bump_version = 'MAJOR'
    elif bump_minor:
        bump_version = 'MINOR'
    elif bump_patch:
        bump_version = 'PATCH'
    else:
        bump_version = None

    next_version = get_next_version(current_version, bump_version, prerelease)

    if not next_version:
        msg = "no changes found; version number not updated"
        raise click.ClickException(msg)

    return next_version


def read_unreleased_changelog_entries(project):
    """Returns entries stored in the unreleased changelog entries dir."""

    dirpath = project.unreleased_changes_path

    if not os.path.exists(dirpath):
        msg = "changelog entries directory {} does not exist.".format(dirpath)
        raise click.ClickException(msg)

    try:
        entries = read_changelog_entries(dirpath)
    except Exception as exc:
        raise click.ClickException(exc)

    return entries


def write_version_number(filepath, version):
    """Write version number to the given file."""

    values = {
        'timestamp': datetime.datetime.utcnow(),
        'version': version
    }
    stream = VERSION_FILE_TEMPLATE.format(**values)

    with open(filepath, mode='w') as fd:
        fd.write(stream)


def write_version_number_pyproject(filepath, version):
    """Write version number into the pyproject file."""

    fd = tomlkit.toml_file.TOMLFile(filepath)

    metadata = fd.read()
    poetry_metadata = metadata["tool"]["poetry"]
    poetry_metadata["version"] = str(version)
    fd.write(metadata)


if __name__ == '__main__':
    semverup()
