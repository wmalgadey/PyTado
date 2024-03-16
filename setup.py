#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

here = lambda *a: os.path.join(os.path.dirname(__file__), *a)

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open(here('README.md')).read()
requirements = [x.strip() for x in open(here('requirements.txt')).readlines()]

setup(name='python-tado',
      version='0.17.5',
      description='PyTado from chrism0dwk, modfied by w.malgadey, diplix, michaelarnauts, LenhartStephan, splifter, syssi, andersonshatch, Yippy, p0thi, Coffee2CodeNL, chiefdragon',
      long_description=readme,
      keywords='tado',
      author='chrism0dwk, w.malgadey',
      author_email='chrism0dwk@gmail.com, w.malgadey@gmail.com',
      url='https://github.com/wmalgadey/PyTado',
      install_requires=requirements,
      license="GPL3",
      zip_safe=False,
      platforms=["any"],
      packages=find_packages(),
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Home Automation',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.5'
      ],
      entry_points={
        'console_scripts': [
            'pytado = pytado.__main__:main'
        ]
      },
)
