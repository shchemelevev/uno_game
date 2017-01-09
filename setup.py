# -*- coding: UTF-8 -*-
from setuptools import setup, find_packages
import os
import uno


CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Web Environment',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    "Programming Language :: Python :: 3.5",
]

setup(
    author="Evgenii Shchemelev",
    author_email="shchemelevev@gmail.com",
    name='uno',
    version=uno.__version__,
    description='MMO Uno game',
    long_description=open(
        os.path.join(os.path.dirname(__file__), 'README.md')
    ).read(),
    license='BSD License',
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    tests_require=[],
    packages=find_packages(exclude=["project", "project.*"]),
    include_package_data=True,
    zip_safe=False,
    test_suite='',
)
