from setuptools import setup, find_packages

from os import path, environ
from warnings import warn

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


def version():
    """Returns a valid PEP 440 version string, or an invalid version
    string on error. """
    if "GITHUB_ACTIONS" in environ:
        return github_release()
    else:
        return local_release()


def test_version(sha):
    """Returns a valid PEP 440 version string for use with CI builds.
    """
    from datetime import datetime

    now = datetime.now()
    return str(now.year) + \
        '.' + str(now.month) + \
        '.' + str(now.day) + \
        '.' + str(now.hour) + \
        '.' + str(now.minute) + \
        '.' + str(now.second) + \
        '.dev' + format(int(sha[0:7], 16), 'o')  # convert short sha to octal


def github_release():
    """Returns a git tag for tagged releases, or an automatically
    generated test release number otherwise. """
    # Production release
    tag = environ.get('GITHUB_REF', '')
    if tag.startswith('refs/tags/'):
        return tag.lstrip('refs/tags/')

    # Test release
    return test_version(environ['GITHUB_SHA'])


def find_tags(repo, sha):
    """Returns a list of tags that point to the given commit sha.
    """
    tags = []

    for tag in repo.tags:
        if tag.object.hexsha == sha:
            tags.append(tag.name)

    return tags


def local_release():
    """If everything is commited in the Git stage then this function
    returns the git tag for the current commit if it exists, or a
    automatically generated version based on the date & time for
    CI builds, otherwise an invalid PEP 440 version string is
    returned to prevent uploads to PyPI. """

    # This string is an invalid version per PEP 440, and should be
    # rejected by production and test PyPI
    BAD_RELEASE = 'invalid.version'

    try:
        import git
    except ImportError:
        return BAD_RELEASE

    repo = git.Repo(search_parent_directories=True)
    sha = repo.head.object.hexsha

    if repo.is_dirty():
        warn("Please commit your code before building!")
        return BAD_RELEASE

    tags = find_tags(repo, sha)
    if len(tags) == 1:  # Production release
        return tags[0]
    elif len(tags) > 1:
        warn("Commit has more than one tag: %s" % tags)
        return BAD_RELEASE
    else:  # Test release
        return test_version(repo.head.object.hexsha)


setup(
    name='awscli-login',
    version=version(),
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
