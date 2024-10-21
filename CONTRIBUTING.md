# Contributing to `awscli-login`

Thank you for considering contributing to [Project Name]! 
We are happy to accept your contributions.

## Table of Contents

1. Code of Conduct
2. How to Contribute
   - Reporting Bugs
   - Suggesting Enhancements
   - Submitting Pull Requests
3. Development Setup
   - Prerequisites
   - Installation
   - Running Tests
4. Style Guides
   - Git Commit Messages
   - Python Code Style
5. Additional Resources

## Code of Conduct

See [Code of Conduct](CODE_OF_CONDUCT.md)

## How to Contribute

### Reporting Bugs

Submit a [GitHub Issue](https://github.com/techservicesillinois/awscli-login/issues).

### Suggesting Enhancements

Submit a [GitHub Issue](https://github.com/techservicesillinois/awscli-login/issues).

## Development Setup

### Prerequisites

- Python 3.8 or higher
- [GNU Make](https://www.gnu.org/software/make/)

### Installation

[Instructions on how to install the project]



1. Clone the project with `git`
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

`make test`

#### Testing across supported versions of Python:

`make tox`

#### Integration Tests



## Style Guides

### Git Commit Messages

[Guidelines for writing good commit messages]

### Python Code Style

[Guidelines for writing Python code, e.g., PEP 8]

## Additional Resources

[Links to additional resources, documentation, etc.]



