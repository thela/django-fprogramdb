import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-fprogramdb',
    version='0.2.7.1',
    packages=find_packages(),
    include_package_data=True,
    license='GNU General Public License v3 (GPLv3)',  # example license
    description='A test Django app to structure and get CORDIS data.',
    long_description=README,
    url='https://github.com/thela/django-fprogramdb',
    author='Luigi Mazari Villanova',
    author_email='luigi.mazari@cnr.it',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.9',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP : Indexing/Search',
        'Topic :: Scientific/Engineering',
    ],
)
