import os
import errno
import subprocess
import sys
from setuptools import setup, find_packages
from setuptools.extension import Extension
from setuptools.command.build_ext import build_ext
from distutils.errors import DistutilsPlatformError

install_requires = [
    'imposm.parser',
    'psycopg2',
    'Shapely',
]

if sys.version_info < (2, 6):
    install_requires.append('multiprocessing')

class build_ext_with_cython(build_ext):
    def generate_c_file(self):
        try:
            print 'creating imposm/cache/tc.c'
            proc = subprocess.Popen(
                ['cython', 'imposm/cache/tc.pyx'],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        except OSError, ex:
            if ex.errno == errno.ENOENT:
                print "Could not find cython command."
                raise DistutilsPlatformError("Failed to generate "
                    "C files with cython.")
            else:
                raise
        out = proc.communicate()[0]
        result = proc.wait()
        if result != 0:
            print "Error during C files generation with cython:"
            print out
            raise DistutilsPlatformError("Failed to generate "
                "C files with cython.")
    def run(self):
        try:
            self.generate_c_file()
        except DistutilsPlatformError:
            if os.path.exists('imposm/cache/tc.c'):
                print 'Found existing C file. Ignoring previous error.'
            else:
                raise
        build_ext.run(self)

import imposm.version
version = imposm.version.__version__

setup(
    name = "imposm",
    version = version,
    description='OpenStreetMap importer for PostGIS.',
    long_description=open('README').read() + open('CHANGES').read(),
    author = "Oliver Tonnhofer",
    author_email = "olt@omniscale.de",
    url='http://imposm.org/',
    license='Apache Software License 2.0',
    packages=find_packages(),
    namespace_packages = ['imposm'],
    include_package_data=True,
    package_data = {'': ['*.xml']},
    install_requires=install_requires,
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: C",
        "Programming Language :: C++",
        "Programming Language :: Python :: 2.5",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    ext_modules=[
        Extension("imposm.cache.tc", ["imposm/cache/tc.c"], libraries = ["tokyocabinet"]),
    ],
    entry_points = {
        'console_scripts': [
            'imposm = imposm.app:main',
            'imposm-psqldb = imposm.psqldb:main',
        ],
    },
    cmdclass={'build_ext':build_ext_with_cython},
)
