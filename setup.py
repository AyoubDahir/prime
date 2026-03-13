from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in prime/__init__.py
from prime import __version__ as version

setup(
	name="prime",
	version=version,
	description="Prime",
	author="Prime",
	author_email="prime",
	packages=find_packages(include=["prime", "prime.*"]),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
