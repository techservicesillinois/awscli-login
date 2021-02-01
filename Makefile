PACKAGE_NAME := awscli-login

PKG  := src/awscli_login
TPKG := src/tests
MODULE_SRCS := $(wildcard $(PKG)/*.py)
export TSTS := $(wildcard $(TPKG)/*.py $(TPKG)/*/*.py)
export SRCS := $(wildcard $(MODULE_SRCS) setup.py)
HTML = htmlcov/index.html
TOX := tox -e wheel -qq --skip-pkg-install
TOX_ENV := .tox/wheel/pyvenv.cfg
WHEEL = $(wildcard dist/*.whl)
PIP = python -m pip install --upgrade --upgrade-strategy eager

.PHONY: all check install test lint static develop develop-coverage
.PHONY: freeze shell clean docs coverage doctest win-tox

all: test coverage docs doctest

# Python dependencies needed for local development
deps: deps-build deps-doc deps-test deps-publish

# Python packages needed to run the tests on a Unix system
deps-posix: deps
	$(PIP) tox-pyenv

# Python packages needed to run the tests on a Windows system
deps-win: deps
	$(PIP) pyenv-win

# Python packages needed to build a wheel
deps-build: deps-publish
	$(PIP) setuptools tox wheel flake8 mypy

# Python packages needed to build the documentation
deps-doc:
	$(PIP) Sphinx sphinx-autodoc-typehints sphinx_rtd_theme

# Python packages needed to run tests
deps-test:
	$(PIP) coverage

# Python packages needed to publish a production or test release
deps-publish:
	$(PIP) twine

# Build wheel and source tarball for upload to PyPI
build: README.rst $(SRCS)
	python setup.py sdist bdist_wheel
	@touch $@

check: .twinecheck
.twinecheck: build
	twine check --strict dist/*
	@touch $@

# Install wheel into tox virtualenv for testing
install: $(TOX_ENV)
$(TOX_ENV): build | cache
	tox -e wheel --notest --installpkg $(WHEEL) -vv
	@touch $@

# Build and save dependencies for reuse
# https://packaging.python.org/guides/index-mirrors-and-caches/#caching-with-pip
# https://www.gnu.org/software/make/manual/make.html#Prerequisite-Types
cache: setup.py | build
	pip wheel --wheel-dir=$@ $(WHEEL) $(WHEEL)[test] coverage
	@touch $@

# Run tests on multiple versions of Python (POSIX only)
tox: .python-version build | cache
	tox --installpkg $(WHEEL)

.python-version:
	pyenv install -s 3.5.10
	pyenv install -s 3.6.12
	pyenv install -s 3.7.9
	pyenv install -s 3.8.6
	pyenv install -s 3.9.0
	pyenv local 3.5.10 3.6.12 3.7.9 3.8.6 3.9.0

# Run tests on multiple versions of Python (Windows only)
win-tox: .win-tox build | cache
	tox --installpkg $(WHEEL)

.win-tox:
	pyenv install 3.5.4 3.6.8 3.7.9 3.8.7 3.9.1
	python scripts/windows_bat.py 3.5.4 3.6.8 3.7.9 3.8.7 3.9.1
	touch $@

# Run tests against wheel installed in virtualenv
test: lint static check .coverage

# Run tests with coverage tool -- generates .coverage file
.coverage: $(TOX_ENV) $(TSTS)
	$(TOX)
	@touch $@

# Show coverage report
coverage: .coverage
	$(TOX) -- coverage report --omit='*/.tox/*,tests/*' --fail-under 80

# Run tests directly against source code in develop mode
develop: lint static .install develop-coverage

# Install package in develop mode
.install: setup.py
	pip install -e .[test]
	@touch $@

.coverage.develop: export COVERAGE_FILE=.coverage.develop
.coverage.develop: $(MODULE_SRCS) $(TSTS)
	coverage run -m unittest discover -s src -v

develop-coverage: export COVERAGE_FILE=.coverage.develop
develop-coverage: .coverage.develop
	@coverage report

lint: .lint
.lint: $(SRCS) $(TSTS)
	flake8 $?  # Test only files that have been updated
	@touch $@

static: .static
.static:$(SRCS) $(TSTS)
	mypy $?  # Test only files that have been updated
	@touch $@

freeze: $(TOX_ENV)
	$(TOX) -- pip freeze

shell: $(TOX_ENV)
	$(TOX) -- bash

report: $(HTML)
$(HTML): .coverage
	$(TOX) -- coverage html

docs: $(SRCS) $(TSTS)
	make -C docs html

doctest: $(SRCS) $(TSTS)
	make -C docs doctest

.PHONY: test-release release .release
RELEASE = $(filter %.whl %.tar.gz, $(wildcard dist/$(PACKAGE_NAME)-*))

test-release: MSG := Please build a test release!
test-release: NOT := not
test-release: export TWINE_REPOSITORY ?= testpypi
test-release: .release

release: MSG := Please tag & build a production release!
release: NOT :=
release: .release

.release:
	@echo "$(RELEASE)" | python -c \
        "import sys; \
        [print('$(MSG)') or exit(1) for l in sys.stdin if 'dev' $(NOT) in l or \
        'invalid' in l];"
	twine upload "$(RELEASE)"

clean:
	rm -rf .coverage .coverage.develop .lint  .mypy_cache .static .tox .wheel htmlcov
	rm -rf $(PKG)/__pycache__ $(TPKG)/__pycache__ $(TPKG)/cli/__pycache__/ $(TPKG)/config/__pycache__
	rm -rf build dist src/*.egg-info .eggs
	make -C docs clean

clean-all: clean
	rm -rf cache
