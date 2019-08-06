import logging
import traceback
import os
import sys
import signal
import pickle
import base64
import subprocess
import shlex
import tempfile
import atexit

''' This was taken daemoniker._daemonize_windoows library as the class was 'protected' 
    and wanted to ensure that the functionality didn't get removed
    in a future patch of daemoniker since it wasn't meant to be public
    
    LICENSING
-------------------------------------------------

daemoniker: Cross-platform daemonization tools.
    Copyright (C) 2016 Muterra, Inc.
    
    Contributors
    ------------
    Nick Badger
        badg@muterra.io | badg@nickbadger.com | nickbadger.com

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the
    Free Software Foundation, Inc.,
    51 Franklin Street,
    Fifth Floor,
    Boston, MA  02110-1301 USA

------------------------------------------------------
    '''
class _LocalNamespacePasser:
    ''' Creates a path in a secure temporary directory, such that the
    path can be used to write in a reentrant manner. Upon context exit,
    the file will be overwritten with zeros, removed, and then the temp
    directory cleaned up.

    We can't use the normal tempfile stuff because:
    1. it doesn't zero the file
    2. it prevents reentrant opening

    Using this in a context manager will return the path to the file as
    the "as" target, ie, "with _ReentrantSecureTempfile() as path:".
    '''

    def __init__(self):
        ''' Store args and kwargs to pass into enter and exit.
        '''
        seed = os.urandom(16)
        self._stem = base64.urlsafe_b64encode(seed).decode()
        self._tempdir = None
        self.name = None

    def __enter__(self):
        try:
            # Create a resident tempdir
            self._tempdir = tempfile.TemporaryDirectory()
            # Calculate the final path
            self.name = self._tempdir.name + '/' + self._stem
            # Ensure the file exists, so future cleaning calls won't error
            with open(self.name, 'wb'):
                pass

        except:
            if self._tempdir is not None:
                self._tempdir.cleanup()

            raise

        else:
            return self.name

    def __exit__(self, exc_type, exc_value, exc_tb):
        ''' Zeroes the file, removes it, and cleans up the temporary
        directory.
        '''
        try:
            # Open the existing file and overwrite it with zeros.
            with open(self.name, 'r+b') as f:
                to_erase = f.read()
                eraser = bytes(len(to_erase))
                f.seek(0)
                f.write(eraser)

            # Remove the file. We just accessed it, so it's guaranteed to exist
            os.remove(self.name)

        # Warn of any errors in the above, and then re-raise.
        except:
            logger.error(
                'Error while shredding secure temp file.\n' +
                ''.join(traceback.format_exc())
            )
            raise

        finally:
            self._tempdir.cleanup()
