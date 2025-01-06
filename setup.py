from setuptools import setup, find_packages


with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='pangolin',
    version='0.1.0',
    description='An SDK to automate IQ and OQ procedures for software based on FDA guidelines',
    long_description='''
    The FDA IQ/OQ SDK is a Python package that provides a set of tools and utilities to automate the Installation Qualification (IQ) and Operational Qualification (OQ) procedures for software systems in compliance with FDA guidelines.

    Key features:
    - Automated IQ checks for software installation and environment setup
    - Automated OQ tests for software functionality and performance
    - Customizable test suites and configurations
    - Detailed reporting and documentation generation
    - Seamless integration with popular continuous integration and delivery (CI/CD) pipelines
    - Compliance with FDA guidelines and best practices for software validation

    This SDK is designed to streamline the validation process for software systems in regulated industries, such as pharmaceutical, biotech, and medical devices. It helps ensure that the software meets the required quality standards and regulatory requirements.
    ''',
    long_description_content_type='text/markdown',
    author='Manish Kumar Bobbili',
    author_email='manishkumar.bobbili3@gmail.com',
    url='https://github.com/yourusername/your_sdk_name',
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='fda iq oq software validation testing compliance',
    python_requires='>=3.6',
)