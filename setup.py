# -*- coding: utf-8 -*-

"""
To upload to PyPI, PyPI test, or a local server:
python setup.py bdist_wheel upload -r <server_identifier>
"""

import setuptools
from distutils.extension import Extension

setuptools.setup(
    name="dedcode_atmenmanip",
    version="0.1.4",
    author="Andreas Postl",
    author_email="dedicated.codes@gmail.com",
    description= "A Nion swift plug-in for atom manipulation using an STEM (ATMEN project)",
    packages=["nionswift_plugin.atmenmanip", "atmenmanip_demo"],
    py_modules = [],
    ext_modules = [],
    install_requires=["dedcode_imgrecog", "dedcode_pathfind",\
                      "numpy", "scipy", "matplotlib"],
    license='GPLv3',
    classifiers=[
        "Development Status :: 1 - Alpha",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.6",
    ],
    include_package_data=True,
    python_requires='~=3.6',
    zip_safe=False,
    dependency_links=["https://github.com/arpostl/dedcode.niswex.imgrecog/tarball/master#egg=dedcode_imgrecog",
                      "https://github.com/arpostl/dedcode.niswex.pathfind/tarball/master#egg=dedcode_pathfind"]
)
