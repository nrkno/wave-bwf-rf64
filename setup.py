#!/usr/bin/env python
# -*- coding: utf-8 -*-
from distutils.core import setup
setup(name='wave_bwf_rf64',
      version='1.1.0',
      description=u'Python modules for handling the Broadcast Wave Format and RF64 files.',
      classifiers=[
          'Development Status :: 3 :: Beta',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
          'Topic :: Multimedia :: Sound/Audio'
      ],
      url='https://github.com/nrkno/wave-bwf-rf64/',
      author='David Marston',
      author_email='david.marston@bbc.co.uk',
      license="GNU GPLv3",
      py_modules=['wave_bwf_rf64', 'chunk'],
      python_requires=">=3.10",
      )
