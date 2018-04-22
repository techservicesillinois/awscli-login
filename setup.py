from setuptools import setup, find_packages

from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='awscli-login',
    version='0.1.0a2',  # TODO change this to a git tag for Drone
    description='A SAML login plugin for awscli.',
    long_description=long_description,
    url='https://github.com/cites-illinois/aws-cli-saml-login',
    author='David D. Riddle',
    author_email='ddriddle@illinois.edu',
    classifiers=[
#        'Development Status :: 4 - Beta',
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='Amazon AWS SAML login access keys',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    install_requires=[
       'awscli',
       'boto3',
       'botocore',
       'daemoniker',
       'keyring',
       'lxml',
       'requests',
    ],
    extras_require={
        'test': [
            'coverage',
            'wurlitzer',
            'tblib',
            'Sphinx',
            'sphinx_rtd_theme',
            'sphinx-autodoc-typehints',
        ],
    },
    test_suite="tests",
    project_urls={
        'Bug Reports':
            'https://github.com/cites-illinois/aws-cli-saml-login/issues',
        'Source': 'https://github.com/cites-illinois/aws-cli-saml-login',
    },
)
