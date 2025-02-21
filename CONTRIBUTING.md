# Contributing to `awscli-login`

Thank you for considering contributing to awscli-login!
We are happy to accept your contributions.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [How to Contribute](#how-to-contribute)
   - [Reporting Bugs](#reporting-bugs)
   - [Suggesting Enhancements](#suggesting-enhancements)
3. [Development Setup](#development-setup)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
   - [Running Tests](#running-tests)
4. [Style Guides](#style-guides)
   - [Git Commit Messages](#git-commit-messages)
   - [Python Code Style](#python-code-style)

## Code of Conduct

See [Code of Conduct](CODE_OF_CONDUCT.md)

## How to Contribute

### Reporting Bugs

Submit a [GitHub Issue](https://github.com/techservicesillinois/awscli-login/issues).

### Suggesting Enhancements

Submit a [GitHub Issue](https://github.com/techservicesillinois/awscli-login/issues).

## Development Setup

### Prerequisites

- Python 3.9 or higher
- [GNU Make](https://www.gnu.org/software/make/)

### Installation

1. Fork and clone the project with `git`
2. (Recommended) Create a Python Virtual Env

	```sh
	$ python -m venv venv
	$ source venv/bin/activate
	```

> Tip: Our `Makefile` expects the command `python` to be aliased to your preferred version of Python3.

3. Build 

	```sh
	(venv) $ make deps
	(venv) $ make build
	```

> Tip: The `Makefile` may warn about missing `setuptools_scm` toward the start of the `deps` step. This can be safely ignored.

4. Run the unit tests to verify the environment

	```sh
	(venv) $ make test
	...

	Ran 109 tests in 0.889s

	OK
	```

4. Install

	```sh
	(venv) $ pip install .
	...
	Successfully installed awscli-login-0.2b2.dev79 lxml-5.3.0
	```

> Tip: `pip install -e .` will not work for running integration tests with AWS CLI.


### Running Tests

#### Unit Tests
To run the unit and static tests against your current python run:

`$ make test`

#### Testing across supported versions of Python:
The test across multiple supported versions of python install [pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation). Then run the following commands:

`$ make .python-version`
`$ make tox`

## Style Guides

### Git Commit Messages

Because we create our 'CHANGELOG.md' from our git logs, we have a standard for our git logs. This standard applies to commits that make it into the \`master\` branch, so please apply it, in particular, when closing a pull request.
 
*   First line of the commit should be short and sweet, and customer focused.
*   Commit details should be formatted as a bulleted list, and developer focused.
*   Commit details should include GitHub keywords such as 'Closes #123' to maintain CHANGELOG links to GitHub issue numbers on a separate final un-bulleted line.

### Python Code Style

The project uses PEP-8 as enforced by flake8.

[PEP-08 Style Guidelines](https://www.python.org/dev/peps/pep-0008/)

[Flake8 lint tool](https://flake8.pycqa.org/en/latest/)




