#!/usr/bin/env python

import subprocess
from setuptools import setup, find_packages

install_cmd = "sudo apt-get install wkhtmltopdf"
subprocess.check_call(install_cmd, shell=True)

setup(
    name='Oski',
    version='1.0',
    description='Oski archives articles of Cal football placekickers.',
    url='https://github.com/mbanderson/Oski',
    author='mbanderson',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'pdfkit',
        'jsonschema',
        'functools32',
        'tldextract',
        'google-api-python-client'
    ]
)