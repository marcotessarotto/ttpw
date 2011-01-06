#!/bin/env python
# -*- coding: utf-8 -*-
# Author: Laurent Pointal <laurent.pointal@limsi.fr> <laurent.pointal@laposte.net>

from distutils.core import setup
import sys


setup(name='treetaggerwrapper',
    version='1.0',
    author='Laurent Pointal',
    author_email='laurent.pointal@limsi.fr',
    url='http://perso.limsi.fr/pointal/dev:treetaggerwrapper',
    download_url='https://sourcesup.cru.fr/projects/ttpw/',
    description='Wrapper for the TreeTagger text annotation tool from H.Schmid.',
    package_dir={'': 'xxxxx'},
    py_modules=['xxxxx'],
    provides=['xxxxx'],
    keywords=['tagger','treetagger','wrapper','text','annotation','linguistic'],
    license='GNU General Public License v2 or greater',
    classifiers=[
                'Development Status :: 5 - Production/Stable',
                'Intended Audience :: Science/Research',
                'Natural Language :: English',
                'Operating System :: OS Independent',
                'Programming Language :: Python :: 2',
                'License :: OSI Approved :: GNU General Public License (GPL)',
                'Topic :: Scientific/Engineering',
                'Topic :: Scientific/Engineering :: Information Analysis',
                ],
    long_description="""\
Python wrapper for TreeTagger, a language independent part-of-speech tagger
---------------------------------------------------------------------------

Wrap the Helmut Schmid tool into a Python class allowing to tag several texts
one after the other, maintaining connexions with the tagger process to speed-up
processing.

Can do the chunking within the wrapper methods, or using an external tool (and
provide directly tokens to the tagger).

Using objects, can start multiple taggers simultaneously, eventually using
different languages.

Support chunking for:

  - english
  - french
  - deutch
  - spanish

This version is based on Python 2.

Treetagger itself is is freely available for research, education and evaluation.
See http://www.ims.uni-stuttgart.de/projekte/corplex/TreeTagger/DecisionTreeTagger.html
""",
    )

