from setuptools import setup, find_packages

requirements = [
    "loguru",
    "numpy",
    "matplotlib",
    "astropy",
    "PySide2",
    "scipy",
    "pypdf2",
    "pdfkit",
    "markdown",
]


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="azcam",
    version="20.2",
    description="azcam",
    long_description=long_description,
    author="Michael Lesser",
    author_email="mlesser@arizona.edu",
    keywords="ccd imaging astronomy observation observatory",
    packages=find_packages(),
    zip_safe=False,
    install_requires=requirements,
)
