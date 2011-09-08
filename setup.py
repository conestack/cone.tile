from setuptools import setup, find_packages
import sys, os

version = '0.9'
shortdesc = 'Handle web application parts as tiles.'
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
longdesc = open(os.path.join(os.path.dirname(__file__), 'src', 'cone', 'tile',
                                                        '_api.rst')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'LICENSE.rst')).read()

setup(name='cone.tile',
      version=version,
      description=shortdesc,
      long_description=longdesc,
      classifiers=[
            'Development Status :: 4 - Beta',
            'Environment :: Web Environment',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
      ],
      keywords='',
      author='BlueDynamics Alliance',
      author_email='dev@bluedynamics.com',
      url=u'https://github.com/bluedynamics/cone.tile',
      license='GNU General Public Licence',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['cone'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'pyramid',
      ],
      extras_require = dict(
          test=['interlude']
      ),
      tests_require=['interlude'],
      test_suite="cone.tile.tests.test_suite",
      )
