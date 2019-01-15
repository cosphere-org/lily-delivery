#!/usr/bin/env python

import os.path
from setuptools import setup, find_packages

from lily_delivery import __version__

requirements_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'requirements.txt')


setup(
    name='lily-delivery',
    description='Lily extension for enabling easy and smart code delivery.',
    version=__version__,
    author='CoSphere Tech Team',
    url='https://github.com/cosphere-org/lily-delivery',
    packages=find_packages(),
    entry_points='''
        [console_scripts]
        lily_delivery=lily_delivery.cli:cli
    ''',
    install_requires=open(requirements_path).readlines(),
    package_data={'': ['requirements.txt']},
    include_package_data=True)
