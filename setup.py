# -*- coding: utf-8 -*-
from setuptools import setup

packages = [
    "pangolin_sdk",
    "pangolin_sdk.configs",
    "pangolin_sdk.connections",
    "pangolin_sdk.utils",
    "pangolin_sdk.validations",
]

package_data = {"": ["*"]}

install_requires = [
    "cx-oracle>=8.3.0,<9.0.0",
    "kubernetes>=32.0.0,<33.0.0",
    "mysql-connector-python>=9.2.0,<10.0.0",
    "paramiko>=3.5.1,<4.0.0",
    "psycopg2-binary>=2.9.10,<3.0.0",
    "pyjwt>=2.10.1,<3.0.0",
    "requests>=2.32.3,<3.0.0",
    "sqlalchemy>=2.0.38,<3.0.0",
]

extras_require = {
    "dev": [
        "black>=25.1.0,<26.0.0",
        "pytest>=8.3.4,<9.0.0",
        "coverage>=7.6.12,<8.0.0",
        "pylint>=3.3.4,<4.0.0",
        "poetry2setup>=1.1.0,<2.0.0",
    ]
}

setup_kwargs = {
    "name": "pangolin-sdk",
    "version": "0.1.0",
    "description": "Developing a unified validation and verification system for IQ that automates testing across databases, SSH, APIs, Kubernetes, AWS, and Azure",
    "long_description": "",
    "author": "Manish Kumar Bobbili",
    "author_email": "manishkumar.bobbili3@gmail.com",
    "maintainer": "None",
    "maintainer_email": "None",
    "url": "None",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "extras_require": extras_require,
    "python_requires": ">=3.11,<4.0",
}


setup(**setup_kwargs)
