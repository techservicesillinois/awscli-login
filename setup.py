from setuptools import setup, find_packages

from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


def version():
    from setuptools_scm.version import get_local_dirty_tag

    def clean_scheme(version):
        # If code is not commited add +dirty to version to prevent
        # upload to either PyPY or test PyPY.
        return get_local_dirty_tag(version) if version.dirty else ''

    return {'local_scheme': clean_scheme}


setup(
    name='awscli-login',
    use_scm_version=version,
    setup_requires=['setuptools_scm'],
    description='Plugin for the AWS CLI that retrieves and rotates '
    'credentials using SAML ECP and STS.',
    long_description=long_description,
    url='https://github.com/techservicesillinois/awscli-login',
    author='David D. Riddle',
    author_email='ddriddle@illinois.edu',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
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
            'tblib',
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
