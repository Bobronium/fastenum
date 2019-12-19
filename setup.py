import os

from setuptools import setup

CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(CURRENT_DIR, 'README.md'), 'r') as f:
    README = f.read()

setup(
    name='fastenum',
    version='0.0.1',
    description='Patch for builtin enum module to achieve best performance',
    long_description=README,
    author='MrMrRobat',
    author_email='appkiller16@gmail.com',
    url='https://github.com/MrMrRobat/fastenum',
    packages=['fastenum'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
