#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016-2021 B-Open Solutions srl - http://bopen.eu
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import codecs
import os

from setuptools import find_packages, setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding='utf-8').read()


setup(
    name='elevation',
    author='B-Open Solutions srl, Alessandro Amici',
    author_email='info@bopen.eu',
    license='Apache License Version 2.0',
    url='https://elevation.bopen.eu',
    project_urls={
        'Sponsor': 'https://bopen.eu',
    },
    description="Download, cache and clip global terrain digital elevation models: "
    "Terrain Tiles, SRTM GL1 ellipsoidal and SRTM 90m DEMs.",
    long_description=read('README.rst'),
    long_description_content_type="text/x-rst",
    packages=find_packages(),
    include_package_data=True,
    install_requires=['appdirs', 'click', 'fasteners'],
    extras_require={'reference': ['fiona', 'rasterio']},
    zip_safe=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Scientific/Engineering :: GIS',
    ],
    keywords='script download SRTM DEM DTM global digital elevation terrain model',
    entry_points={'console_scripts': ['eio=elevation.cli:eio']},
)
