# Release Tools [![Build Status](https://github.com/Bitergia/release-tools/workflows/tests/badge.svg)](https://github.com/Bitergia/release-tools/actions?query=workflow:tests+branch:master+event:push) [![Coverage Status](https://coveralls.io/repos/github/Bitergia/release-tools/badge.svg?branch=master)](https://coveralls.io/github/Bitergia/release-tools?branch=master)
Set of tools to generate Python releases.

With this package, Python maintainers are able to automate
many of the boring and time consuming tasks related with
packages and releases.

These tools are based in the way GitLab project generates its
releases. You have more information about their motivation
[here](https://gitlab.com/gitlab-org/gitlab-foss/issues/17826).

This software is licensed under GPL3 or later.


## Features

This package allows us to:

 * Automate the creation of release notes
 * Bump up the release version based on the release notes
 * Publish a release in a Git repository


## Requirements

 * Python >= 3.7
 * Poetry >= 1.0


## Installation

To install the release tools from the source code you'll need
to install `poetry`. We use [poetry](https://python-poetry.org/)
for dependency management and packaging. You can install it
following its [documentation](https://python-poetry.org/docs/#installation).

Once you have installed it, you can download the source code with git:

```
# Get release-tools source code
$ git clone https://github.com/Bitergia/release-tools
```

Move to the directory and install the software and the dependencies:

```
$ cd release-tools
$ poetry install
```

## Workflow

Together with these tools, this package provides an **opinionated
way** to generate the release of a Python package. We think
releases must be automated and provide useful information
to end users so they can understand better the changes between
versions. Our tools fulfill those requirements.

There are also some **assumptions** to take into account:

* We use git repositories.
* We use [semantic versioning](https://semver.org/) for numbering our packages.\
  Version numbers are defined in the variable `__version__` which is
  stored on a file called `_version.py`. This file must be tracked on the git
  repository.
* We use `poetry` and the file `pyproject.toml`
  (see [PEP518](https://www.python.org/dev/peps/pep-0518/)) to manage
  build system dependencies. If you don't have this file, you can use
  the command `poetry init` to create it from scratch. This file must
  be tracked on the git repository.

The **workflow** is defined by the next steps:

```
    changelog -> semverup -> notes -> publish
```

- Developers use `changelog` script to generate changelog **entry
  notes**. They contain basic information about their changes in
  the code (e.g a new feature; a fixed bug). The notes should
  **explain** the change to a reader who has **zero context** about
  software details.\
  We **recommend** to create one of these entries for each pull
  request or merge request.\
  These notes are stored under the directory `releases/unreleased`.
- Once we are ready to create a new release, we call `semverup`.
  It will increase the **version** according to semantic versioning
  and the type of changelog entries generated between releases.
- When the version is increased, we run `notes` to generate the
  **release notes** using the unreleased changelog entries.
- Finally, we **publish** the release in the Git repository creating
  a **commit** that will contain the new release notes and the new
  version files. A **tag** is also created with the new version number.
  To do it, we call to `publish` script. This script also removes
  the entries in `released/unreleased` directory.

This is an example of the basic usage:
```
# Create some changelog entries
$ changelog -t "Fix bug #666" -c fixed
Changelog entry 'fix-bug-#666.yml' created

$ changelog -t "Add support for deleting entries" -c added
Changelog entry 'add-support-for-deleting-entries.yml' created

# Increase the version number
$ semverup
0.2.0

# Generate the release notes
$ notes "WebApp" 0.2.0
Release notes file '0.2.0.md' created

# Publish the release in a public repository
$ publish 0.2.0 "John Smith <jsmith@example.com>" --push origin
Cleaning directories...done
Adding files to the release commit...done
Creating release commit...done
Publishing release in origin...done
```

## Tools

### changelog

This interactive tool creates note entries about the changes in
the code. Developers can use this tool to create these notes that
will be included in the changelog or in the release notes.
You will need to run this script inside of the Git where you store
the project.

It will guide you to create a new entry. You can select the title
and the type of the change.

```
>> Please specify the title of your change: Fix bug #666
```
```
>> Please specify the category of your change

1. New feature (added)
2. Bug fix (fixed)
3. Breaking change (changed)
4. New deprecation (deprecated)
5. Feature removal (removed)
6. Security fix (security)
7. Performance improvement (performance)
8. Dependencies updated (dependency)
9. Other (other)

: 2
```

Each category updates a different version number:
- Major version: `changed` and `removed`.
- Minor version: `added`, `deprecated`, `security`, `performance` and `other`.
- Patch version: `fixed` and `dependency`.

At the end of the process, a text editor will open to let you review
the entry and make the final changes. The editor will be the default
defined in your system.

```
title: 'Fix bug #666'
category: fixed
author: John Smith <jsmith@example.com>
issue: 666
notes: >
  The bug was making impossible to cast a spell on
  a magician.
```

New entries will be stored in "releases/unreleased" directory.
This directory must be available under the Git root path.

```
Changelog entry 'fix-bug-#666.yml' created
```

If you don't want to create a new entry and see only the final result,
please active '--dry-run' flag.

```
$ changelog --dry-run
```

You can skip some parts of the process providing information
in advance such as the title (`-t`) or the category (`-c`)
of the entry.

```
$ changelog -t "Fix bug #666" -c fixed
```

### semverup

This script increments the version number following semver specification
and using the note entries generated with `changelog` tool.

```
$ semverup
0.2.0
```

### notes

When you run this script, it will generate the release notes of the
package tracked by the current Git repository.

You'll need to provide the `name` of the package and the `version`
of the new release. The script will generate a Markdown document
under the `releases` directory using the changelog entries stored
on `releases/unreleased`. Take into account the argument `name`
is only used as the title of the document.

```
$ notes "MyApp" 0.2.0
Release notes file '0.2.0.md' created
```

Changelog entries included in the release notes are moved to a new
directory in 'unreleased/processed'. If you are running multiple
release candidates, and you don't want to include the same notes in
successive release candidates, use the flag '--pre-release'.

If you also want to add the content of these release notes to the `NEWS`
file, use the flag `--news`.

```
$ notes "MyApp" 0.2.0 --news
Release notes file '0.2.0.md' created
News file updated to 0.2.0
```

If you just want to see the final result of the notes
but not generate a new file, please activate `--dry-run` flag.

```
$ notes "MyApp" 0.2.0 --dry-run
## MyApp 0.2.0 - (2020-03-04)

**Bug fixes:**

 * Fix bug #666
   The bug was making impossible to cast a spell on
   a magician.
```

If you want to add the contributor names of these release notes to the 
AUTHORS file, use the flag `--authors`.

```
$ notes "MyApp" 0.2.0 --authors
Release notes file '0.2.0.md' created
Authors file updated
```

### publish

This script will generate a new release in the repository.
This will consist on creating a commit and a tag with the
new release notes and the updated version files.

To run it, you'll need to provide the version number and
the author of the new release.

```
$ publish 0.2.0 "Jonh Smith <jsmith@example.com>"
Cleaning directories...done
Adding files to the release commit...done
Creating release commit...done
```

By default the command doesn't push the commit release to a
remote repository. To force it, use the parameter `--push`
including the name of the remote where commits will be pushed.

```
$ publish 0.2.0 "John Smith <jsmith@example.com>" --push origin
Cleaning directories...done
Adding files to the release commit...done
Creating release commit...done
Publishing release in origin...done
```

It is also possible to push only the commit release and its tag.
To do so, set `--only-push` together with `--push` option.

```
$ publish 0.2.0 "John Smith <jsmith@example.com>" --push origin --only-push
Publishing release in origin...done
```


## Troubleshooting

### How can I change the default editor used by `changelog`?

By default, `changelog` will use the editor defined in the `EDITOR`
environment variable. You can define your own editor updating this
variable.

```
export EDITOR=/bin/nano
```

If this variable doesn't exist it will try with `vim` or `nano`
in that order.

### What's the format of the changelog entries?

Changelog entries use  [YAML format](https://yaml.org/).

Remember you can write blocks of text using `>` character at the beginning
of each block. See the next example:

```
title: 'Example of notes'
category: fixed
author: John Smith <jsmith@example.com>
issue: 1
notes: >
  Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod
  tempor incididunt ut labore et dolore magna aliqua.
  Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi
  ut aliquip ex ea commodo consequat.
```

### Error: version file not found

The tools did not found a `_version.py` file. This file must also
be tracked on your repository. It must contain a variable named
`__version__`. The value must be a string following semantic
versioning format.

```
$ cat _version.py
__version__ = "3.6.5"
```

### Error: version number '\<version\>' in '\<filepath\>' is not a valid semver string

The format of the version number is invalid. We use semantic
versioning format to set version numbers. The value must be a `str`.
Change the version number and check the
[semantic versioning rules](https://semver.org/) in case of doubt.


### Error: pyproject file not found

The tools did not found a `pyproject.toml` file. This file must also
be tracked on your repository. It contains information needed by `poetry`
to build the software package. If you don't have this file
you can create a new one using `poetry init`.

```
$ poetry init
```

### Error: pathspec '\<filepath\>' did not match any files; code error: 128

The file `<filepath>` must be tracked by your git repository. Add it to
your repo. Usually you'll get this error if you forgot to add your
changelog entry notes to the repository.

### Error: tag '\<tag\>' already exists; code error: 128

If you have a existing tag with the same version, you can expect 
this error. You can delete the tag using `git tag -d version` and 
create the release commit again using publish.

```
$ git tag -d 0.2.0
$ publish 0.2.0 "John Smith <jsmith@example.com>" --push origin
```

### Error: error: src refspec '\<branch\>' does not match any

You can expect this error if you are not using `master` as your default 
branch. You can change this in the codebase (push method of the publish.py) 
if you are using any other branch as default.

If you are using `main` as default branch, change `master` to `main`.

```
-   project.repo.push(remote, 'master')
+   project.repo.push(remote, 'main')
```

You can use `publish` and set `--only-push` together with `--push` option 
as the release is committed but not pushed yet.

```
$ publish 0.2.0 "John Smith <jsmith@example.com>" --push origin --only-push
Publishing release in origin...done
```


### Error: Authentication failed for '\<github-url\>'; code error: 128

If the release commit is created and you failed to publish the release 
because of invalid credentials for git, you can use `publish` and 
set `--only-push` together with `--push` option as the release is committed
but not pushed yet.

```
$ publish 0.2.0 "John Smith <jsmith@example.com>" --push origin --only-push
Publishing release in origin...done
```


## License

Licensed under GNU General Public License (GPL), version 3 or later.
