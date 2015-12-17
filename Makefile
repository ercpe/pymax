TARGET?=tests

test_default_python:
	PYTHONPATH=".:./src" python tests/ -v

test_py2:
	@echo Executing test with python2
	PYTHONPATH=".:./src" python2 tests/ -v

test_py3:
	@echo Executing test with python3
	PYTHONPATH=".:./src" python3 tests/ -v

test: test_py2 test_py3

compile:
	@echo Compiling python code
	python -m compileall src/

compile_optimized:
	@echo Compiling python code optimized
	python -m compileall src/

travis: compile compile_optimized test_default_python

coverage:
	coverage erase
	PYTHONPATH=".:./src" coverage run --source='src' --omit='src/test.py,src/fakecube.py' --branch tests/__main__.py
	coverage report -m
