PACKAGE_NAME := awscli-login

PKG  := src/awscli_login
TPKG := src/tests
export TSTS := $(wildcard $(TPKG)/*.py $(TPKG)/*/*.py)
export SRCS := $(wildcard $(PKG)/*.py)
OBJS := $(patsubst %.py,%.pyc,$(SRCS))
VENV := venv
HTML = htmlcov/index.html

.PHONY: all install test clean test-all docs

all: build test html

install: build
	pip install -e .

build: $(OBJS) setup.py
	python setup.py build

%.pyc: %.py
	python -m compileall -b $<

test: .report
	@cat $?

.report: .coverage
	@coverage report > $@

.coverage: $(SRCS) $(TSTS)
	flake8 $^
	mypy $^
	@coverage run setup.py test || rm $@
#	@coverage combine

html: $(HTML)

docs: $(SRCS) $(TSTS)
	make -C docs html

doctest:
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
	rm -rf .coverage .report .summary __pycache__ htmlcov .mypy_cache
	rm -rf $(TPKG)/__pycache__ $(PKG)/__pycache__ $(TPKG)/config/__pycache__
	rm -rf $(TPKG)/*.pyc  $(PKG)/*.pyc
	rm -rf build dist venv src/*.egg-info .eggs
