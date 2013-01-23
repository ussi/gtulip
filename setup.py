import os
import sys
import logging
from setuptools import setup, find_packages

version='0.1'

install_requires = ['setuptools',
                    'gunicorn >= 0.17.2',
                    ]

tests_require = install_requires + ['nose']

def read(f):
    return open(os.path.join(os.path.dirname(__file__), f)).read().strip()


setup(name='gtulip',
      version=version,
      description=('Tulip based Gunicorn worker.'),
      long_description='\n\n'.join((read('README.rst'), read('CHANGES.txt'))),
      classifiers=[
          "License :: OSI Approved :: MIT License",
          "Intended Audience :: Developers",
          "Programming Language :: Python",
          "Programming Language :: Python :: 3.3",
          "Programming Language :: Python :: Implementation :: CPython",
          "Topic :: Internet :: WWW/HTTP",
          'Topic :: Internet :: WWW/HTTP :: WSGI'],
      author='Nikolay Kim',
      author_email='fafhrd91@gmail.com',
      url='https://github.com/fafhrd91/gtulip/',
      license='MIT',
      packages=find_packages(),
      install_requires = install_requires,
      tests_require = tests_require,
      test_suite = 'nose.collector',
      include_package_data = True,
      zip_safe = False,
      entry_points = {
          'paste.server_runner': [
              'server = gtulip.paster:tulip_server_runner',
              ],
          },
      )
