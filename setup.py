#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
	name='pymax',
	version='0.4',
	description='Python implementation of the ELV MAX! Cube API',
	author='Johann Schmitz',
	author_email='johann@j-schmitz.net',
	url='https://ercpe.de/projects/pymax',
	download_url='https://github.com/ercpe/pymax/tarball/0.4',
	packages=find_packages('src'),
	package_dir={'': 'src'},
	include_package_data=True,
	zip_safe=False,
	license='GPL-3',
)
