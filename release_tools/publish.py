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
#     Venu Vardhan Reddy Tekula <venu@bitergia.com>
#

"""
Script to publish a new release.

The script will publish a new release in the repository.
It will commit the version number and the new changelog file,
and creating a new tag for the release.
"""

import os

import click

from release_tools.entry import read_changelog_entries
from release_tools.project import Project
from release_tools.repo import RepositoryError


@click.command()
@click.argument('version')
@click.argument('author')
@click.option('--push', 'remote', help="Push release to the given remote.")
@click.option('--only-push', is_flag=True,
              help="Do not generate a release commit; push the existing one.")
def publish(version, author, remote, only_push):
    """Publish a new release.

    This script will generate a new release in the repository.
    This will consist on creating a commit and a tag with the
    new release notes and the updated version files.

    To run it, you will need to provide the version number and
    the author of the new release.

    By default the command does not push the commit release to a
    remote repository. To force it, use the parameter `--push`
    including the name of the remote where commits will be pushed.

    It is also possible to push only the commit release and its tag.
    To do so, set '--only-push' together with '--push' option.

    VERSION: version of the new release.

    AUTHOR: author of the new release (e.g. John Smith <jsmith@example.com>)
    """
    if only_push and not remote:
        msg = "'--only-push' flag must be set together with '--push'"
        raise click.ClickException(msg)

    try:
        project = Project(os.getcwd())
    except RepositoryError as e:
        raise click.ClickException(e)

    try:
        if not only_push:
            remove_unreleased_changelog_entries(project)
            add_release_files(project, version)
            commit(project, version, author)

        if remote:
            push(project, remote, version)
    except RepositoryError as e:
        raise click.ClickException(e)


def remove_unreleased_changelog_entries(project):
    """Delete changelog entries files included within the release."""

    click.echo("Cleaning directories...", nl=False)

    dirpath = project.unreleased_changes_path

    if not os.path.exists(dirpath):
        click.echo("done")
        return

    entries = read_changelog_entries(dirpath).keys()

    for filename in entries:
        filepath = os.path.join(dirpath, filename)
        project.repo.rm(filepath)

    click.echo("done")


def rollback_add_release_files(project):
    click.echo("rollback to the last consistent state")
    project.repo.restore_staged()
    try:
        project.repo.restore_unstaged(project.unreleased_changes_path)
    except RepositoryError:
        pass


def add_release_files(project, version):
    """Add to the repository all the files needed to publish a release."""

    click.echo("Adding files to the release commit...", nl=False)

    # Add version file
    version_file = project.version_file

    if not version_file:
        rollback_add_release_files(project)
        raise click.ClickException("version file not found")

    project.repo.add(version_file)

    # Add pyproject.toml file
    pyproject_file = project.pyproject_file

    if not pyproject_file:
        rollback_add_release_files(project)
        raise click.ClickException("pyproject file not found")

    project.repo.add(pyproject_file)

    # Add release notes file
    notes_file = os.path.join(project.releases_path, version + '.md')

    if not os.path.exists(notes_file):
        msg = "release notes file {} not found".format(notes_file)
        rollback_add_release_files(project)
        raise click.ClickException(msg)

    project.repo.add(notes_file)

    # Add NEWS file
    news_file = project.news_file

    if not os.path.exists(news_file):
        msg = "news file not found"
        rollback_add_release_files(project)
        raise click.ClickException(msg)

    project.repo.add(news_file)

    # Add AUTHORS file
    authors_file = project.authors_file

    if not os.path.exists(authors_file):
        msg = "authors file not found"
        rollback_add_release_files(project)
        raise click.ClickException(msg)

    project.repo.add(authors_file)

    click.echo("done")


def rollback_commit(project):
    click.echo("rollback to the last consistent state")
    project.repo.reset_head()
    try:
        project.repo.restore_unstaged(project.unreleased_changes_path)
    except RepositoryError:
        pass


def commit(project, version, author):
    """Add a release commit and tag."""

    click.echo("Creating release commit...", nl=False)

    try:
        msg = "Release {}".format(version)
        project.repo.commit(msg, author)
        project.repo.tag(version)
    except RepositoryError as e:
        rollback_commit(project)
        raise click.ClickException(e)

    click.echo("done")


def push(project, remote, release_tag):
    """Publish the release in the given remote repository."""

    click.echo("Publishing release in {}...".format(remote), nl=False)

    project.repo.push(remote, 'master')
    project.repo.push(remote, release_tag)

    click.echo("done")


if __name__ == '__main__':
    publish()
