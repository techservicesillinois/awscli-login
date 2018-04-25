PACKAGE_NAME := awscli-login

PKG  := src/awscli_login
TPKG := src/tests
export TSTS := $(wildcard $(TPKG)/*.py $(TPKG)/*/*.py)
export SRCS := $(wildcard $(PKG)/*.py)
OBJS := $(patsubst %.py,%.pyc,$(SRCS))
VENV := venv
HTML = htmlcov/index.html

.PHONY: all install test clean test-all docs coverage doctest

all: build test docs doctest coverage

install: build
	pip install -e .

build: $(OBJS) setup.py
	python setup.py build

%.pyc: %.py
	python -m compileall -b $<

.python-version:
	pyenv install -s 3.5.2
	pyenv install -s 3.6.5
	pyenv local 3.5.2 3.6.5

tox: .python-version
	tox

test: .report
	@cat $?

.report: .coverage
	@coverage report > $@

.coverage: $(SRCS) $(TSTS)
	flake8 $^
	mypy $^
	@coverage run setup.py test || rm $@
#	@coverage combine

coverage: $(HTML)

docs: $(SRCS) $(TSTS)
	make -C docs html

doctest: $(SRCS) $(TSTS)
	make -C docs doctest

$(HTML): .coverage
	@coverage html

test-all: $(VENV)/bin/awscli-login
	(\
		source $(VENV)/bin/activate; \
		python setup.py test; \
	)

$(VENV): build
	virtualenv $@

$(VENV)/bin/awscli-login: $(VENV)
	(\
		source $(VENV)/bin/activate; \
		pip install -r requirements.txt; \
		python setup.py install; \
	)

clean:
	-pip uninstall -y $(PACKAGE_NAME)
	rm -rf .coverage .report .summary __pycache__ htmlcov .mypy_cache .tox
	rm -rf $(TPKG)/__pycache__ $(PKG)/__pycache__ $(TPKG)/config/__pycache__
	rm -rf $(TPKG)/*.pyc  $(PKG)/*.pyc
	rm -rf build dist venv src/*.egg-info .eggs
	make -C docs clean
