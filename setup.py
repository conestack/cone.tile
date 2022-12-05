from setuptools import find_packages
from setuptools import setup
from setuptools.command.test import test
import os


def read_file(name):
    with open(os.path.join(os.path.dirname(__file__), name)) as f:
        return f.read()


version = '1.2.dev0'
shortdesc = 'Tiles for use in pyramid framework.'
longdesc = '\n\n'.join([read_file(name) for name in [
    'README.rst',
    'CHANGES.rst',
    'LICENSE.rst'
]])


class Test(test):

    def run_tests(self):
        from cone.tile import tests
        tests.run_tests()


setup(
    name='cone.tile',
    version=version,
    description=shortdesc,
    long_description=longdesc,
    classifiers=[
        'Environment :: Web Environment',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    keywords='',
    author='Cone Contributors',
    author_email='dev@conestack.org',
    url='http://github.com/conestack/cone.tile',
    license='Simplified BSD',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['cone'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'zope.component',
        'zope.deprecation',
        'zope.exceptions',
        'pyramid>=1.5',
        'pyramid_chameleon',
    ],
    extras_require=dict(test=['zope.testrunner']),
    tests_require=['zope.testrunner'],
    cmdclass=dict(test=Test)
)
