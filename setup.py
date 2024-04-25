#!/usr/bin/env python2

from setuptools import setup, find_packages


def included_package(p):
	return p.startswith('spacq.') or p == 'spacq'


setup(
	name='SpanishAcquisition',
	version='3.0',
	author='Dmitri Iouchtchenko',
	author_email='diouchtc@uwaterloo.ca',
	maintainer='Zach Merino',
	maintainer_email='zmerinog@uwaterloo.ca',
	description='Package for interfacing with devices and building user '
			'interfaces.',
	license='BSD',
	url='https://github.com/mainCSG/SpanishAcquisition3',
	packages=[p for p in find_packages() if included_package(p)],
	classifiers=[
		'Development Status :: 3 - Alpha',
		'Intended Audience :: Science/Research',
		'License :: OSI Approved :: BSD License',
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 3',
	],
)