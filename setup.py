#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
setup(name='wave_bwf_levl_RF64',
      version='1.1.0',
      description=u'Python modules for handling Broadcast Wave Format files. \
      Updated to also handle the levl and md5 chunk and reading of RF64 files. \
      This work was done by Tormod Værvågen of NRK (Norsk rikskringkasing).',
      classifiers=[
          'Development Status :: 3 :: Beta',
          'Programming Language :: Python :: 3.5',
      ],
      url='http://data.bbcarp.org.uk/saqas/',
      author='David Marston',
      author_email='david.marston@bbc.co.uk',
      license="GNU GPLv3",
      py_modules=['wave_bwf_levl_RF64', 'chunk_levl_RF64'],
      python_requires=">=3.10",
      )
