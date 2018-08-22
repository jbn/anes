import codecs
import os
import re

from setuptools import setup, find_packages

###############################################################################

NAME = 'anes'

PACKAGES = find_packages(where=".")

META_PATH = os.path.join("anes", "__init__.py")

KEYWORDS = ["anes", "political science", "social science"]

CLASSIFIERS = [
    "Development Status :: 3 - Alpha",
    "Framework :: IPython",
    "Topic :: Communications",
    "Natural Language :: English",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3.5",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

INSTALL_REQUIRES = ['modpipe']

###############################################################################

SELF_DIR = os.path.abspath(os.path.dirname(__file__))


def read_file_safely(*path_parts):
    with codecs.open(os.path.join(SELF_DIR, *path_parts), "rb", "utf-8") as f:
        return f.read()


META_FILE = read_file_safely(META_PATH)

META_VARS_RE = re.compile(r"^__([_a-zA-Z0-9]+)__ = ['\"]([^'\"]*)['\"]", re.M)

META_VARS = dict(META_VARS_RE.findall(META_FILE))

###############################################################################

if __name__ == "__main__":
    setup(
        name=NAME,
        description=META_VARS["description"],
        license=META_VARS["license"],
        url=META_VARS["uri"],
        version=META_VARS["version"],
        author=META_VARS["author"],
        author_email=META_VARS["email"],
        maintainer=META_VARS["author"],
        maintainer_email=META_VARS["email"],
        keywords=KEYWORDS,
        long_description=read_file_safely("README.rst"),
        packages=PACKAGES,
        package_dir={"": "."},
        include_package_data=True,
        classifiers=CLASSIFIERS,
        install_requires=INSTALL_REQUIRES,
    )
