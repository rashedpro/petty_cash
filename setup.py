from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in petty_cash/__init__.py
from petty_cash import __version__ as version

setup(
	name="petty_cash",
	version=version,
	description="Petty cash request,clearance and accounting",
	author="GreyCube Technologies",
	author_email="admin@greycube.in",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
