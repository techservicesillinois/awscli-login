"""
This script creates several bat files that contain the path to the pyenv install
of each python version. The bat files are then used by tox when running tests on
Windows.
"""

import os
import sys

PYTHON_VERSIONS = {}
PATH = os.environ['USERPROFILE'] + '\\bin'

if len(sys.argv) == 1:
    print('Error. Did not specify python versions.')
    exit(1)

inputs = sys.argv[1:]

for item in inputs:
    major, minor, micro = item.split('.')
    PYTHON_VERSIONS[major + '.' + minor] = item

# create bin folder in userprofile
if not os.path.exists(PATH):
    print(f'No bin folder found. Creating {PATH}.'
          f'Please remember to add this to your user path.')
    os.mkdir(PATH)

os.chdir(PATH)

# Create bat files for each python version
for version in PYTHON_VERSIONS:
    file_name = f'python{version}.bat'
    pyenv_path = (f'%USERPROFILE%\\.pyenv\\pyenv-win\\versions'
                  f'\\{PYTHON_VERSIONS[version]}\\python.exe %*')

    f = open(file_name, 'w+')
    f.writelines(['@echo off\n', pyenv_path])
    f.close()
