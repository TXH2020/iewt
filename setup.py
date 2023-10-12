import codecs
from setuptools import setup
from iewt._version import __version__ as version


with codecs.open('README.rst', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='iewt',
    version=version,
    description='Interactive embedded web terminal',
    long_description=long_description,
    author='Tejas Hegde',
    author_email='1001.tejas@gmail.com',
    url='https://github.com/TXH2020/iewt',
    packages=['iewt'],
    entry_points='''
    [console_scripts]
    iewt = iewt.main:main
    ''',
    license='MIT',
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    install_requires=[
        'requests',
        'tornado>=4.5.0',
        'paramiko>=2.3.1',
    ],
)
