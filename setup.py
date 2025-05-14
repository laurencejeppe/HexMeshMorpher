from setuptools import setup, find_packages
from os import path, walk

def readme():
    """Read the contents of the README file."""
    with open("README.md", "r", encoding="utf-8") as f:
        return f.read()

def requirements():
    """Read the contents of the requirements file."""
    with open("requirements.txt", "r", encoding="utf-8") as f:
        return f.read().splitlines()

setup(
    name="HexMeshMorpher",
    version="0.1.0",
    description="A Python package for morphing hexahedral meshes.",
    package_dir={"": "HexMeshMorpher"},
    packages=find_packages(where="HexMeshMorpher"),
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/laurencejeppe/HexMeshMorpher",
    author="Laurence Russell",
    author_email="l.j.russell@soton.ac.uk",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=requirements(),
    python_requires=">=3.7",
)