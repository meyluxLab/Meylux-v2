PYTHON ?= python3

.PHONY: test compile

test:
	$(PYTHON) -m unittest discover -s tests -v

compile:
	$(PYTHON) -m compileall -q src config tests
