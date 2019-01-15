# Makefile

SHELL := /bin/bash

help:  ## show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

#
# DEVELOPMENT
#
install:
	python -m venv .venv && \
	source .venv/bin/activate && \
	pip install -r requirements.txt && \
	pip install -r test-requirements.txt


#
# TESTS
#
test:  ## run selected tests
	py.test --cov=./lily_env --cov-config .coveragerc -r w -s -vv $(tests)

test_all:  ## run all available tests
	py.test --cov=./lily_env --cov-config .coveragerc -r w -s -vv tests

coverage:  # render html coverage report
	coverage html -d coverage_html && google-chrome coverage_html/index.html
