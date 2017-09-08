import io
import sys

from setuptools import setup


def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


long_description = read('README.rst', 'CHANGES.md')
requirements_test = read('requirements-test.txt').split('\n')

setup(
    name='punq',
    version='0.0.1',
    url='http://github.com/madedotcom/photon-pump/',
    license='MIT',
    author='Bob Gregory',
    tests_require=requirements_test,
    author_email='bob@codefiend.co.uk',
    description='Unintrusive dependency injection for Python 3.6 +',
    long_description=long_description,
    packages=['punq'],
    include_package_data=True,
    platforms='any',
    test_suite='photonpump.test',
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 3 - Alpha',
        'Natural Language :: English',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries :: Application Frameworks'
        ]
)
