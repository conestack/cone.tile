from setuptools import setup, find_packages
import sys, os

version = '1.1'
shortdesc = 'Handle web application parts as tiles.'
longdesc = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()
longdesc = open(os.path.join(os.path.dirname(__file__), 'src', 'bda', 'bfg',
                             'tile', '_api.txt')).read()
longdesc += open(os.path.join(os.path.dirname(__file__), 'LICENSE.rst')).read()

setup(name='cone.tile',
      version=version,
      description=shortdesc,
      long_description=longdesc,
      classifiers=[
            'Development Status :: 3 - Alpha',
            'Environment :: Web Environment',
            'Operating System :: OS Independent',
            'Programming Language :: Python', 
            'Topic :: Internet :: WWW/HTTP :: Dynamic Content',        
      ],
      keywords='',
      author='BlueDynamics Alliance',
      author_email='dev@bluedynamics.com',
      url=u'https://svn.bluedynamics.eu/svn/module/cone.tile/',
      license='GNU General Public Licence',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages=['cone'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'repoze.bfg',
      ],
      # XXX: why should this be set here?
      #dependency_links = [
      #    "http://dist.repoze.org/bfg/1.3/",
      #],
      extras_require = dict(
          test=['interlude']
      ),
      tests_require=['interlude'],
      test_suite="cone.tile.tests.test_suite",      
      )
