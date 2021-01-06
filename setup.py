from setuptools import find_packages, setup

requirements = [
    "loguru",
    "numpy",
    "matplotlib",
    "astropy",
]

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="azcam",
    version="21.1.1",
    description="azcam",
    long_description_content_type="text/markdown",
    long_description=long_description,
    author="Michael Lesser",
    author_email="mlesser@arizona.edu",
    keywords="ccd imaging astronomy observation observatory",
    packages=find_packages(),
    zip_safe=False,
    install_requires=requirements,
)
