"""Setup for the elsametric"""

import setuptools


# with open('README.md') as f:
#     README = f.read()

setuptools.setup(
    author='Pooria Soltani',
    author_email='pooria.ms@gmail.com',
    name='elsametric',
    # license='',
    description='Designs a DB to store academic publications data.',
    version='v0.1.1',
    # long_description=README,
    url='https://github.com/pmsoltani/elsametric',
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    install_requires=[
        'sqlalchemy>=1.3',
        'sqlalchemy-utils>=0.34',
        'mysql-connector-python>=8'
    ],
    classifiers=[
        # Trove classifiers
        # (https://pypi.python.org/pypi?%3Aaction=list_classifiers)
        'Development Status :: 4 - Beta',
        # 'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers',
    ],
)
