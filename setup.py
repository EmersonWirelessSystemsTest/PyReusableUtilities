import pathlib
from setuptools import setup

try:
    import wheel
except ImportError:
    raise ImportError('Run the command "pip install wheel" prior to installing this package')

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(
    name="PyReusableUtilities",
    version="1.1.1",
    description="Contains a collection of libraries and software meant to be reused across projects",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/EmersonWirelessSystemsTest/PyReusableUtilities",
    author="Alex Stangl",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    packages=["PyReusableUtilities"],
    include_package_data=True,
    install_requires=[],
    package_data={},
)
