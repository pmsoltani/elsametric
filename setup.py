"""Setup for the elsametric"""

import setuptools
from elsametric import \
    __name__, \
    __author__, \
    __license__, \
    __version__, \
    __email__, \
    __url__, \
    __description__


# with open('README.md') as f:
#     README = f.read()

setuptools.setup(
    author=__author__,
    author_email=__email__,
    name=__name__,
    license=__license__,
    description=__description__,
    version=__version__,
    # long_description=README,
    url=__url__,
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
