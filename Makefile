PACKAGE_NAME := awscli-login
MODULE_NAME := awscli_login
ifndef SETUPTOOLS_SCM_PRETEND_VERSION_FOR_AWSCLI_LOGIN
VERSION := $(shell python -m setuptools_scm)
else
VERSION := $(SETUPTOOLS_SCM_PRETEND_VERSION_FOR_AWSCLI_LOGIN)
endif

PKG  := src/$(MODULE_NAME)
TPKG := src/tests
MODULE_SRCS := $(wildcard $(PKG)/*.py $(PKG)/plugin/*.py)
export TSTS := $(wildcard $(TPKG)/*.py $(TPKG)/*/*.py)
export SRCS := $(wildcard $(MODULE_SRCS) setup.py)
HTML := htmlcov/index.html
TOX := tox -e wheel -qq --skip-pkg-install
TOX_ENV := .tox/wheel/pyvenv.cfg
WHEEL := $(MODULE_NAME)-$(VERSION)-py3-none-any.whl
SDIST := $(MODULE_NAME)-$(VERSION).tar.gz
RELEASE := dist/$(WHEEL) dist/$(SDIST)
PIP := python -m pip install --upgrade --upgrade-strategy eager

.PHONY: all check install test lint static develop develop-coverage
.PHONY: freeze shell clean docs coverage doctest win-tox
.PHONY: install-build build

all: test coverage docs doctest

# Python dependencies needed for local development
deps: deps-build deps-doc deps-test deps-integration-test deps-publish

# Python packages needed to run the tests on a Windows system
deps-win: deps
	$(PIP) pyenv-win

# Python packages needed to build a wheel
deps-build: deps-publish
	$(PIP) build tox flake8 mypy types-requests rst_include setuptools_scm

# Python packages needed to build the documentation
deps-doc:
	$(PIP) Sphinx sphinx-autodoc-typehints sphinx_rtd_theme rst_include

# Python packages needed to run tests
deps-test:
	$(PIP) coverage

# Python packages needed to run integration_tests tests
deps-integration-test:
	$(PIP) awscli vcrpy

# Python packages needed to publish a production or test release
deps-publish:
	$(PIP) twine

docs/readme.rst:
	make -C docs readme.rst

# Build wheel and source tarball for upload to PyPI
build: $(RELEASE)
$(RELEASE): docs/readme.rst pyproject.toml MANIFEST.in $(SRCS)
	python -m build

check: .twinecheck
.twinecheck: $(RELEASE)
	twine check --strict $^
	@touch $@

# Install wheel into tox virtualenv for testing
install: $(TOX_ENV)
$(TOX_ENV): $(RELEASE) | cache
	tox -e wheel --notest --installpkg dist/$(WHEEL)
	@touch $@

# Build and save dependencies for reuse
# https://packaging.python.org/guides/index-mirrors-and-caches/#caching-with-pip
# https://www.gnu.org/software/make/manual/make.html#Prerequisite-Types
cache: pyproject.toml | $(RELEASE)
	pip wheel --wheel-dir=$@ dist/$(WHEEL)[test] coverage
	@touch $@

# Run tests on multiple versions of Python (POSIX only)
tox: .python-version $(RELEASE) | cache
	tox --installpkg dist/$(WHEEL)

.python-version:
	pyenv install -s 3.9.21
	pyenv install -s 3.10.16
	pyenv install -s 3.11.11
	pyenv install -s 3.12.9
	pyenv install -s 3.13.2
	pyenv local 3.9.21 3.10.16 3.11.11 3.12.9 3.13.2

# Run tests on multiple versions of Python (Windows only)
win-tox: .win-tox $(RELEASE) | cache
	tox --installpkg dist/$(WHEEL)

.win-tox:
	pyenv install 3.9.1
	python scripts/windows_bat.py 3.9.1
	touch $@

# Run tests against wheel installed in virtualenv
test: lint static check .coverage

idp: .idp.docker
.idp.docker:
	docker compose up -d
	@touch $@

idp-down:
	docker compose down --rmi all
	rm -f .idp.docker

.install-build: $(RELEASE)
install-build: .install-build
	pip install dist/$(WHEEL)

# Some integration tests require Linux containers for the
# IdP. HyperV is required by Docker but NOT supported by
# Github Action's Windows VMs.
# https://github.com/actions/runner-images/issues/2216
ifeq ($(RUNNER_OS),Windows)
    idp_integration_deps=
integration-tests integration-tests-v2: export AWSCLI_LOGIN_SKIP_DOCKER_TESTS=1
integration-tests integration-tests-v2: export AWSCLI_LOGIN_WINDOWS_TEST=1
# As of 9/13/2024, macos-latest does not support docker. This may
# change by the end of the year. See issue #208.
else ifeq ($(RUNNER_OS),macOS)
    idp_integration_deps=
integration-tests integration-tests-v2: export AWSCLI_LOGIN_SKIP_DOCKER_TESTS=1
else
    idp_integration_deps=.idp.docker
endif
integration-tests: $(idp_integration_deps)
	aws --version 2>/dev/null | grep '^aws-cli/1.' || (echo "Not running awscli V1!"; exit 1)
	make -C src/integration_tests/

ifeq ($(RUNNER_OS),Windows)
    VBIN := Scripts
    VPKG := lib/site-packages*
else
    VBIN := bin
    VPKG := lib/python*/site-packages
endif
venv.v2: $(RELEASE)
	rm -rf $@
	python -m venv $@
	$@/$(VBIN)/python -m pip install vcrpy $<

integration-tests-v2: export AWSCLI_TEST_V2:=1
integration-tests-v2: export AWSCLI_TEST_PLUGIN_PATH=$(wildcard $(PWD)/venv.v2/$(VPKG))
integration-tests-v2: export PATH:=$(PWD)/venv.v2/$(VBIN):$(PATH)
integration-tests-v2: $(idp_integration_deps) venv.v2
	aws --version 2>/dev/null | grep '^aws-cli/2.' || (echo "Not running awscli V2!"; exit 1)
	make -C src/integration_tests/

test_fast: export AWSCLI_LOGIN_FAST_TEST_ONLY=1
test_fast: .install
	python -m unittest discover --failfast -s src

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
.install: docs/readme.rst pyproject.toml
	pip install -e .[test]
	@touch $@

.coverage.develop: export COVERAGE_FILE=.coverage.develop
.coverage.develop: .install $(MODULE_SRCS) $(TSTS)
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
ERR_TOO_MANY := "Too many releases or invalid release!"
test-release: MSG := Please build a test release!
test-release: NOT := not
test-release: export TWINE_REPOSITORY ?= testpypi
test-release: .release

release: MSG := Please tag & build a production release!
release: NOT :=
release: .release

.release: $(RELEASE)
	@echo "$(RELEASE)" | python -c 'import sys;\
	files = sys.stdin.read().split();\
	len(files) != 2 and (print($(ERR_TOO_MANY)) or exit(1));\
	[print("$(MSG)") or exit(1) for l in files if "dev" $(NOT) in l or "invalid" in l or "dirty" in l]'
	twine upload $(RELEASE)

clean: idp-down
	rm -rf .coverage .coverage.develop .lint .mypy_cache .static .tox .wheel htmlcov .twinecheck .install-build
	rm -rf $(PKG)/__pycache__ $(TPKG)/__pycache__ $(TPKG)/cli/__pycache__/ $(TPKG)/config/__pycache__
	rm -rf build dist src/*.egg-info .eggs
	make -C docs clean

clean-all: clean
	rm -rf cache
