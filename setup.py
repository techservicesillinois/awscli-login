from setuptools import setup, find_packages

from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='co-awscli-login',
    version='0.1.0a7',  # TODO change this to a git tag for Drone
    description='Plugin for the AWS CLI that retrieves and rotates '
    'credentials using SAML ECP and STS.',
    long_description=long_description,
    url='https://github.com/techservicesillinois/awscli-login',
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
    python_requires='>=3.5',
    install_requires=[
       'awscli',
       'boto3',
       'botocore',
       'daemoniker',
       'keyring',
       'lxml',
       'psutil',
       'requests',
    ],
    extras_require={
        'test': [
            'Sphinx',
            'coverage',
            'sphinx-autodoc-typehints',
            'sphinx_rtd_theme',
            'tblib',
            'tox',
            'tox-pyenv',
            'wurlitzer',
        ],
    },
    test_suite="tests",
    project_urls={
        'Bug Reports':
            'https://github.com/techservicesillinois/awscli-login/issues',
        'Source': 'https://github.com/techservicesillinois/awscli-login',
    },
)
