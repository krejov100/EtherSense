from distutils.core import setup

setup(
    name='EtherSense',
    version='0.1dev',
    packages=['tox', 'python-crontab', 'librealsense', ],
    license='Apache License Version 2.0, January 2004',
    long_description=open('README.md').read(),
)


# http://manpages.ubuntu.com/manpages/trusty/man1/run-one.1.html

# https://pypi.org/project/python-crontab/