TARGET?=tests

test_py2:
	@echo Executing test with python2
	PYTHONPATH=".:./src" python2 tests/

test_py3:
	@echo Executing test with python3
	PYTHONPATH=".:./src" python3 tests/

test: test_py2 test_py3

coverage:
	coverage erase
	PYTHONPATH=".:./src" coverage run --source='src' --omit='src/test.py' --branch tests/__main__.py
	coverage report -m
