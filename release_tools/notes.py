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
#     Venu Vardhan Reddy Tekula <venu@bitergia.com>
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
@click.option('--news', is_flag=True,
              help="Update NEWS file with the release notes.")
@click.option('--authors', is_flag=True,
              help="Update AUTHORS file with the release notes.")
@click.option('--pre-release', is_flag=True,
              help="Create pre-release notes; ignores notes from previous release candidates.")
@click.argument('name', callback=validate_argument)
@click.argument('version', callback=validate_argument)
def notes(name, version, dry_run, overwrite, news, authors, pre_release):
    """Generate release notes.

    When you run this script, it will generate the release notes of the
    package tracked by the current Git repository.

    You will need to provide the 'NAME' of the package and the 'VERSION'
    of the new release. The script will generate a Markdown document
    under the 'releases' directory. Take into account the argument `NAME`
    is only used as the title of the document.

    Changelog entries included in the release notes are moved to a new
    directory in 'unreleased/processed'. If you are running multiple
    release candidates, and you don't want to include the same notes in
    successive calls to notes, use the flag '--pre-release'.

    If you also want to add the content of these release notes to the NEWS
    file, use the flag `--news`.

    If you want to add the contributor names of these release notes to the
    AUTHORS file, use the flag `--authors`.

    In the case a release notes file for the same version already exists,
    an error will be raised. Use '--overwrite' to force to replace the
    existing file. If you just want to see the final result of the notes
    but not generate a new file, and not move the changelogs processed,
    please activate '--dry-run' flag.

    NAME: title of the package for the release notes.

    VERSION: version of the new release.
    """
    try:
        project = Project(os.getcwd())
    except RepositoryError as e:
        raise click.ClickException(e)

    entry_list = read_unreleased_changelog_entries(project, pre_release)

    md = compose_release_notes(name, version, entry_list)

    if dry_run:
        click.echo(md)
    else:
        write_release_notes(project, version, md,
                            overwrite=overwrite, news=news)
        move_processed_unreleased_entries(project)

    if authors:
        au_content = compose_author_content(project, entry_list)
        write_authors_file(project, au_content)


def read_unreleased_changelog_entries(project, pre_release):
    """Import changelog entries to include in the notes."""

    dirpath = project.unreleased_changes_path

    if not os.path.exists(dirpath):
        msg = "changelog entries directory '{}' does not exist.".format(dirpath)
        raise click.ClickException(msg)

    try:
        entries = read_changelog_entries(dirpath)
    except Exception as exc:
        raise click.ClickException(exc)

    if not pre_release:
        dirpath = project.unreleased_processed_entries_path
        if os.path.exists(dirpath):
            new_entries = read_changelog_entries(dirpath)
            entries.update(new_entries)

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


def compose_author_content(project, entries):
    """Generate the authors file content."""

    composer = AuthorsFileComposer()
    content = composer.compose(project, entries)

    return content


def write_release_notes(project, version, content,
                        overwrite=False, news=False):
    """Write the release notes."""

    write_release_notes_file(project, version, content, overwrite)

    if news:
        update_news_file(project, version, content)


def write_release_notes_file(project, version, content, overwrite):
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


def write_authors_file(project, content):
    """Write the authors content to the authors file."""

    authors_file = project.authors_file

    with open(authors_file, 'w') as fd:
        fd.write(content)

    click.echo("Authors file updated")


def update_news_file(project, version, content):
    """Update the news file with content of the release notes."""

    news_file = project.news_file

    # Read old content
    try:
        # Skip the title line and read the content
        with open(news_file, 'r') as fd:
            fd.readline()
            original_content = fd.read()
    except FileNotFoundError:
        original_content = ''

    content = content.strip('\n')
    original_content = original_content.strip('\n')

    with open(news_file, 'w') as fd:
        fd.write("# Releases\n\n")
        fd.write("{}\n\n".format(content))

        if original_content:
            fd.write("\n{}\n\n".format(original_content))

    click.echo("News file updated to {}".format(version))


def move_processed_unreleased_entries(project):
    """Move processed entries to a new directory for future release notes"""

    src_dirpath = project.unreleased_changes_path
    dest_dirpath = project.unreleased_processed_entries_path

    try:
        os.makedirs(dest_dirpath, mode=0o755)
    except FileExistsError:
        pass

    for filename in os.listdir(src_dirpath):
        if filename.endswith('.yml'):
            src_filepath = os.path.join(src_dirpath, filename)
            dest_filepath = os.path.join(dest_dirpath, filename)
            project.repo.mv(src_filepath, dest_filepath)


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
    ENTRY_DESC_PR_TEMPLATE = " * {desc} (#{issue})"
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

        if entry.issue:
            content = self.ENTRY_DESC_PR_TEMPLATE.format(desc=entry.title,
                                                         issue=entry.issue)
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
        """Order entries by issue identifier."""

        # Entries with empty issue will be pushed to the end of the list
        return sorted(entries, key=lambda e: int(e.issue) if e.issue else sys.maxsize)


class AuthorsFileComposer:
    """Authors file content composer."""

    def compose(self, project, entries):
        """Generate authors file content from release notes."""

        authors = self._extract_authors(project)

        def _check_author_exists_already(author):
            if author not in authors:
                authors.append(author)

        for _, entry_list in sorted(entries.items()):
            for entry in ReleaseNotesComposer._sort_entries_by_id(entry_list):
                if not entry.author:
                    continue

                if type(entry.author) is list:
                    for author in entry.author:
                        _check_author_exists_already(author)
                else:
                    _check_author_exists_already(entry.author)

        content = ""

        for author in authors:
            content += author + "\n"

        content += "\n"

        return content

    def _extract_authors(self, project):
        """Extract authors from the authors file."""

        authors_file = project.authors_file

        # Read old content
        try:
            with open(authors_file, 'r') as fd:
                authors = fd.read().splitlines()
                authors = [author for author in authors if author]
        except FileNotFoundError:
            authors = []

        return authors


if __name__ == "__main__":
    notes()
