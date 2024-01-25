from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ["--cov", "smartcsv", "tests/"]

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import sys, pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)

setup(
    name='smartcsv',
    version='0.1.4',
    description="CSVs are awesome, yet they're pretty dumb. Let's get them smarter!",
    url='http://github.com/santiagobasulto/smartcsv',
    download_url="https://github.com/santiagobasulto/smartcsv/tarball/0.1.4",
    author='Santiago Basulto',
    author_email='santiago.basulto@gmail.com',
    license='MIT',
    packages=['smartcsv'],
    maintainer='Santiago Basulto',
    tests_require=[
        'cov-core==1.14.0',
        'coverage==3.7.1',
        'py==1.4.23',
        'pytest==2.6.1',
        'pytest-cov==1.8.0',
        'six==1.7.3'
    ],
    zip_safe=False,
    cmdclass={'test': PyTest},
)