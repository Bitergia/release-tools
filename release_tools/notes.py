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
Script to generate the release notes of a package.

It will read the changelog entries stored under 'releases/unreleased'
directory and will generate a file with the list of changes.
The script needs the name of the package and the version to release.
"""

import datetime
import os
import sys
import textwrap

import click

from release_tools.entry import (CategoryChange,
                                 read_changelog_entries)
from release_tools.project import Project
from release_tools.repo import RepositoryError


def validate_argument(ctx, param, value):
    """Check argument valid values."""

    value = value.strip("\n\r ")

    if not value:
        raise click.BadParameter("cannot be empty")
    return value


@click.command()
@click.option('--dry-run', is_flag=True,
              help="Do not write release notes file. Print to the standard output instead.")
@click.option('--overwrite', is_flag=True,
              help="Force to replace an existing release notes entry.")
@click.argument('name', callback=validate_argument)
@click.argument('version', callback=validate_argument)
def notes(name, version, dry_run, overwrite):
    """Generate release notes.

    When you run this script, it will generate the release notes of the
    package tracked by the current Git repository.

    You will need to provide the 'NAME' of the package and the 'VERSION'
    of the new release. The script will generate a Markdown document
    under the 'releases' directory. Take into account the argument `NAME`
    is only used as the title of the document.

    In the case a release notes file for the same version already exists,
    an error will be raised. Use '--overwrite' to force to replace the
    existing file. If you just want to see the final result of the notes
    but not generate a new file, please activate '--dry-run' flag.

    NAME: title of the package for the release notes.

    VERSION: version of the new release.
    """
    try:
        project = Project(os.getcwd())
    except RepositoryError as e:
        raise click.ClickException(e)

    entry_list = read_unreleased_changelog_entries(project)

    md = compose_release_notes(name, version, entry_list)

    if dry_run:
        click.echo(md)
    else:
        write_release_notes(project, version, md, overwrite=overwrite)


def read_unreleased_changelog_entries(project):
    """Import changelog entries to include in the notes."""

    dirpath = project.unreleased_changes_path

    if not os.path.exists(dirpath):
        msg = "changelog entries directory '{}' does not exist.".format(dirpath)
        raise click.ClickException(msg)

    try:
        entries = read_changelog_entries(dirpath)
    except Exception as exc:
        raise click.ClickException(exc)

    entries = organize_entries_by_category(entries)

    return entries


def organize_entries_by_category(entry_list):
    """Sort entries by category."""

    entries = {}

    for _, entry in entry_list.items():
        entries.setdefault(entry.category.value, []).append(entry)

    return entries


def compose_release_notes(title, version, entries):
    """Generate the release notes content."""

    composer = ReleaseNotesComposer()
    content = composer.compose(title, version, entries)
    return content


def write_release_notes(project, version, content, overwrite=False):
    """Write the release notes text to a file."""

    if not content:
        msg = "Aborting due to empty release notes"
        raise click.ClickException(msg)

    mode = 'w' if overwrite else 'x'

    filepath = determine_release_notes_filepath(project, version)

    try:
        filename = os.path.basename(filepath)

        with open(filepath, mode=mode) as f:
            f.write(content)
    except FileExistsError:
        msg = ("Release notes for version {} already exist. "
               "Use '--overwrite' to replace it.").format(version)
        raise click.ClickException(msg)
    else:
        click.echo("Release notes file '{}' created".format(filename))

    return filepath


def determine_release_notes_filepath(project, version):
    """Determine the file path for the release notes."""

    dirpath = project.basepath
    dirpath = os.path.join(dirpath, 'releases')
    filepath = os.path.join(dirpath, version + '.md')

    return filepath


class ReleaseNotesComposer:
    """Markdown release notes composer."""

    HEADLINE_TEMPLATE = "## {title} {version} - ({date})\n\n"
    CATEGORY_TITLE_TEMPLATE = "**{title}:**\n\n"
    ENTRY_DESC_PR_TEMPLATE = " * {desc} (#{pr})"
    ENTRY_DESC_NO_PR_TEMPLATE = " * {desc}"
    NOTES_INDENT = "   "
    EMPTY_NOTES_TEMPLATE = "No changes list available.\n"

    def compose(self, title, version, entries):
        """Generate release notes using markdown format."""

        headline = self._compose_headline(title, version)
        sections = []

        for category in CategoryChange:
            sublist = entries.get(category.value, None)

            if not sublist:
                continue

            sections.append(self._compose_category_section(category,
                                                           sublist))

        if sections:
            content = headline + "\n".join(sections)
        else:
            content = headline + self.EMPTY_NOTES_TEMPLATE

        content += '\n'

        return content

    def _compose_headline(self, title, version):
        """Generate the headline of the document."""

        metadata = {
            'title': title,
            'version': version,
            'date': self._datetime_utcnow_str()
        }

        return self.HEADLINE_TEMPLATE.format(**metadata)

    def _compose_category_section(self, category, entries):
        """Generate a section with the entries of a given category."""

        header = self._compose_category_title(category)
        section = [
            self._compose_entry(entry)
            for entry in self._sort_entries_by_id(entries)
        ]
        content = header + "".join(section)

        return content

    def _compose_category_title(self, category):
        """Generate the category title for a section."""

        suffix = 's' if not category.title.endswith('x') else 'es'
        title = category.title + suffix

        return self.CATEGORY_TITLE_TEMPLATE.format(title=title)

    def _compose_entry(self, entry):
        """Generate the changelog entry text."""

        if entry.pr:
            content = self.ENTRY_DESC_PR_TEMPLATE.format(desc=entry.title,
                                                         pr=entry.pr)
        else:
            content = self.ENTRY_DESC_NO_PR_TEMPLATE.format(desc=entry.title)

        if entry.notes:
            notes_text = textwrap.indent(textwrap.fill(entry.notes),
                                         self.NOTES_INDENT)
            content += "\\\n" + notes_text

        content += "\n"

        return content

    @staticmethod
    def _datetime_utcnow_str():
        """Get a formatted string of the current datetime."""

        return datetime.datetime.utcnow().strftime("%Y-%m-%d")

    @staticmethod
    def _sort_entries_by_id(entries):
        """Order entries by PR identifier."""

        # Entries with empty PR will be pushed to the end of the list
        return sorted(entries, key=lambda e: int(e.pr) if e.pr else sys.maxsize)


if __name__ == "__main__":
    notes()
